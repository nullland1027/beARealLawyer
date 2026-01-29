from __future__ import annotations

from pathlib import Path
from typing import List

import streamlit as st

from core.enums import STATUSES
from core.file_links import normalize_file_paths, resolve_missing_paths, select_local_files, select_local_folder
from core.models import Project
from core.repository import ProjectRepository
from core.service import ProjectService
from ui.components import render_metrics, render_project_detail

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "projects.json"
CARD_FIELD_OPTIONS = ["当事人", "相对人", "阶段", "承办律师", "状态", "完成度"]
DEFAULT_CARD_FIELDS = ["当事人", "相对人", "阶段"]


def _filter_projects(projects: List[Project], status: str, keyword: str) -> List[Project]:
    result = projects
    if status and status != "全部":
        result = [item for item in result if item.status == status]
    if keyword:
        needle = keyword.strip().lower()
        if needle:
            result = [
                item
                for item in result
                if needle in item.name.lower()
                or needle in item.client.lower()
                or needle in item.opponent.lower()
                or needle in item.lawyer.lower()
            ]
    return result


def _append_selected_files(state_key: str) -> None:
    selected = select_local_files()
    if not selected:
        st.info("未选择文件。")
        return
    existing = st.session_state.get(state_key, "")
    lines = [line for line in existing.splitlines() if line.strip()]
    lines.extend(selected)
    st.session_state[state_key] = "\n".join(lines)
    st.success(f"已添加 {len(selected)} 个文件路径。")


def _build_project_name(client: str, opponent: str) -> str:
    name = f"{client} 对 {opponent}".strip()
    return name or "新项目"


def _ensure_state(key: str, value: object) -> None:
    if key not in st.session_state:
        st.session_state[key] = value


def _format_card_value(project: Project, label: str) -> str:
    if label == "项目名称":
        return project.name or "未命名项目"
    if label == "当事人":
        return project.client or "未填写"
    if label == "相对人":
        return project.opponent or "未填写"
    if label == "阶段":
        return project.stage or "未填写"
    if label == "承办律师":
        return project.lawyer or "未填写"
    if label == "状态":
        return project.status or "未填写"
    if label == "完成度":
        return f"{project.completion}%"
    return ""


@st.dialog("项目详情")
def render_detail_dialog(project: Project) -> None:
    render_project_detail(project)


@st.dialog("删除项目")
def render_delete_dialog(repo: ProjectRepository, project: Project) -> None:
    st.error("删除后不可恢复。")
    st.caption(f"请输入项目名称以确认删除：{project.name}")
    confirmation = st.text_input("项目名称确认")
    if st.button("确认删除", type="primary"):
        if confirmation != project.name:
            st.error("项目名称不匹配，未删除。")
            return
        if repo.delete(project.id):
            st.success("项目已删除。")
            st.rerun()
        else:
            st.warning("项目不存在或已删除。")


@st.dialog("编辑项目")
def render_edit_dialog(repo: ProjectRepository, service: ProjectService, project: Project) -> None:
    prefix = f"edit_{project.id}"
    name_key = f"{prefix}_name"
    client_key = f"{prefix}_client"
    opponent_key = f"{prefix}_opponent"
    lawyer_key = f"{prefix}_lawyer"
    stage_key = f"{prefix}_stage"
    completion_key = f"{prefix}_completion"
    status_key = f"{prefix}_status"
    notes_key = f"{prefix}_notes"
    file_paths_key = f"{prefix}_file_paths"

    _ensure_state(name_key, project.name)
    _ensure_state(client_key, project.client)
    _ensure_state(opponent_key, project.opponent)
    _ensure_state(lawyer_key, project.lawyer)
    _ensure_state(stage_key, project.stage)
    _ensure_state(completion_key, project.completion)
    _ensure_state(status_key, project.status if project.status in STATUSES else STATUSES[0])
    _ensure_state(notes_key, project.notes)
    _ensure_state(file_paths_key, "\n".join([file.path for file in project.files]))

    # 文件和文件夹选择按钮
    col_file, col_folder = st.columns(2)
    if col_file.button("📄 选择文件", key=f"{prefix}_select_files"):
        _append_selected_files(file_paths_key)
    if col_folder.button("📁 选择文件夹", key=f"{prefix}_select_folder"):
        selected_folder = select_local_folder()
        if selected_folder:
            # 将文件夹路径添加到文件路径列表中
            existing = st.session_state.get(file_paths_key, "")
            lines = [line for line in existing.splitlines() if line.strip()]
            lines.append(selected_folder)
            st.session_state[file_paths_key] = "\n".join(lines)
            st.toast(f"已添加文件夹：{selected_folder}")

    with st.form(f"edit_project_form_{project.id}", clear_on_submit=False):
        name = st.text_input("项目名称", key=name_key)
        client = st.text_input("当事人", key=client_key)
        opponent = st.text_input("相对人", key=opponent_key)
        lawyer = st.text_input("承办律师", key=lawyer_key)
        stage = st.text_input("阶段", key=stage_key)
        completion = st.slider("完成情况（%）", 0, 100, key=completion_key)
        status = st.selectbox("状态", STATUSES, key=status_key)
        notes = st.text_area("备注", key=notes_key)
        st.divider()
        st.caption("文件和文件夹路径（每行一个，支持文件和文件夹混合）")
        st.text_area("路径列表", key=file_paths_key, height=120)
        submitted = st.form_submit_button("保存修改")

    if not submitted:
        return

    if not name.strip():
        st.error("请填写项目名称。")
        return

    file_paths = normalize_file_paths(st.session_state.get(file_paths_key, ""))
    updated = service.build_project(
        name=name.strip(),
        client=client.strip(),
        opponent=opponent.strip(),
        lawyer=lawyer.strip(),
        stage=stage.strip(),
        completion=completion,
        status=status,
        notes=notes.strip(),
        file_paths=file_paths,
        project_id=project.id,
    )
    updated.created_at = project.created_at
    repo.update(updated)

    missing = resolve_missing_paths(file_paths)
    if missing:
        st.warning(f"有 {len(missing)} 个路径不存在，请确认后再编辑。")
    st.toast("项目已更新。")
    st.rerun()


def render_dashboard(repo: ProjectRepository, service: ProjectService, projects: List[Project]) -> None:
    st.subheader("案件/项目看板")
    with st.sidebar:
        with st.expander("项目统计", expanded=True):
            render_metrics(projects)
        with st.expander("卡片字段", expanded=False):
            selected = st.session_state.get("card_fields")
            if selected:
                sanitized = [field for field in selected if field in CARD_FIELD_OPTIONS]
                if not sanitized:
                    sanitized = DEFAULT_CARD_FIELDS
                if sanitized != selected:
                    st.session_state["card_fields"] = sanitized
            st.multiselect(
                "展示字段",
                CARD_FIELD_OPTIONS,
                default=DEFAULT_CARD_FIELDS,
                key="card_fields",
                help="可多选，项目名称始终显示在卡片顶部。",
            )
        
        # 危险区域
        with st.expander("⚠️ 危险区域", expanded=False):
            st.warning("此区域包含危险操作，请谨慎使用！")
            
            # 初始化确认状态
            if "delete_all_step" not in st.session_state:
                st.session_state["delete_all_step"] = 0
            
            step = st.session_state["delete_all_step"]
            
            if step == 0:
                if st.button("🗑️ 删除全部项目", type="secondary", use_container_width=True):
                    st.session_state["delete_all_step"] = 1
                    st.rerun()
            elif step == 1:
                st.error("⚠️ 第一次确认：你确定要删除所有项目吗？")
                col1, col2 = st.columns(2)
                if col1.button("确认删除", type="primary", key="confirm_1"):
                    st.session_state["delete_all_step"] = 2
                    st.rerun()
                if col2.button("取消", key="cancel_1"):
                    st.session_state["delete_all_step"] = 0
                    st.rerun()
            elif step == 2:
                st.error("⚠️ 第二次确认：此操作不可恢复！")
                col1, col2 = st.columns(2)
                if col1.button("我确定要删除", type="primary", key="confirm_2"):
                    st.session_state["delete_all_step"] = 3
                    st.rerun()
                if col2.button("取消", key="cancel_2"):
                    st.session_state["delete_all_step"] = 0
                    st.rerun()
            elif step == 3:
                st.error("⚠️ 最后确认：请输入 'DELETE' 以确认删除所有项目")
                confirm_text = st.text_input("输入 DELETE 确认", key="delete_confirm_text")
                col1, col2 = st.columns(2)
                if col1.button("执行删除", type="primary", key="confirm_3"):
                    if confirm_text == "DELETE":
                        count = repo.delete_all()
                        st.session_state["delete_all_step"] = 0
                        st.success(f"已删除 {count} 个项目！")
                        st.rerun()
                    else:
                        st.error("输入不正确，请输入 'DELETE'")
                if col2.button("取消", key="cancel_3"):
                    st.session_state["delete_all_step"] = 0
                    st.rerun()

    filter_col, search_col = st.columns([1, 2])
    status_filter = filter_col.selectbox("状态筛选", ["全部"] + STATUSES)
    keyword = search_col.text_input("关键词搜索（项目名/当事人/承办律师）")

    filtered = _filter_projects(projects, status_filter, keyword)
    if not filtered:
        st.info("暂无项目，可以点击上方“新建项目”按钮创建。")
        return

    st.markdown("#### 项目卡片")
    selected_fields = st.session_state.get("card_fields", DEFAULT_CARD_FIELDS)
    detail_fields = [label for label in CARD_FIELD_OPTIONS if label in selected_fields]
    
    # 三列布局：等待接手 | 正在处理 | 已结案
    col_waiting, col_processing, col_closed = st.columns(3, gap="large")
    status_columns = {
        "等待接手": col_waiting,
        "正在处理": col_processing,
        "已结案": col_closed,
    }
    
    # 为每列添加标题
    for status, col in status_columns.items():
        with col:
            st.markdown(f"##### {status}")
    
    # 按状态分组，在对应列中纵向排列卡片
    for status in STATUSES:
        group = [p for p in filtered if p.status == status]
        col = status_columns.get(status)
        if not col:
            continue
        with col:
            for project in group:
                with st.container(border=True):
                    st.markdown(f"**{_format_card_value(project, '项目名称')}**")
                    for label in detail_fields:
                        st.caption(f"{label}：{_format_card_value(project, label)}")
                    button_col1, button_col2, button_col3 = st.columns(3, gap="small")
                    if button_col1.button(
                        "详情",
                        key=f"detail_{project.id}",
                        help="详情",
                        type="secondary",
                        use_container_width=True,
                    ):
                        render_detail_dialog(project)
                    if button_col2.button(
                        "编辑",
                        key=f"edit_{project.id}",
                        help="编辑",
                        type="secondary",
                        use_container_width=True,
                    ):
                        render_edit_dialog(repo, service, project)
                    if button_col3.button(
                        "删除",
                        key=f"delete_{project.id}",
                        help="删除",
                        type="secondary",
                        use_container_width=True,
                    ):
                        render_delete_dialog(repo, project)


@st.dialog("初始化新项目")
def render_create_dialog(repo: ProjectRepository, service: ProjectService) -> None:
    st.caption("初始化仅需填写关键信息，文件路径等可在编辑中补充。")

    with st.form("create_project_form", clear_on_submit=True):
        client = st.text_input("当事人")
        opponent = st.text_input("相对人")
        lawyer = st.text_input("承办律师")
        notes = st.text_area("备注（可选）")
        submitted = st.form_submit_button("创建项目")

    if not submitted:
        return

    if not client.strip():
        st.error("请填写当事人。")
        return
    if not opponent.strip():
        st.error("请填写相对人。")
        return
    if not lawyer.strip():
        st.error("请填写承办律师。")
        return

    name = _build_project_name(client.strip(), opponent.strip())
    project = service.build_project(
        name=name,
        client=client.strip(),
        opponent=opponent.strip(),
        lawyer=lawyer.strip(),
        stage="",
        completion=0,
        status=STATUSES[0],
        notes=notes.strip(),
        file_paths=[],
    )
    repo.add(project)
    st.success("项目已创建。")
    st.rerun()


def render_app() -> None:
    repo = ProjectRepository(DATA_FILE)
    service = ProjectService()

    st.title("律师案件管理")
    st.caption("本地文件链接 + 项目状态管理的初版看板")
    st.markdown(
        """
<style>
/* 侧边栏展开面板 - 移除边框 */
div[data-testid="stExpander"] {
  border: none !important;
  background: transparent !important;
}
div[data-testid="stExpander"] details {
  border: none !important;
}
div[data-testid="stExpander"] summary {
  border: none !important;
}

/* 移除指标卡片的多余样式 */
div[data-testid="stMetric"] {
  background: transparent !important;
  border: none !important;
}

/* 项目卡片 - 圆角矩形边框 */
section[data-testid="stMain"] div[data-testid="column"] > div > div[data-testid="stVerticalBlockBorderWrapper"] {
  background: #ffffff !important;
  border: 1px solid #d0d0d0 !important;
  border-radius: 12px !important;
  padding: 16px !important;
  box-shadow: none !important;
  margin-bottom: 8px;
}

/* 项目卡片内的按钮行 */
section[data-testid="stMain"] div[data-testid="column"] div[data-testid="stButton"] {
  margin: 0 !important;
  padding: 0 !important;
}
section[data-testid="stMain"] div[data-testid="column"] button {
  margin: 0 !important;
}
section[data-testid="stMain"] div[data-testid="column"] div[data-testid="stHorizontalBlock"] {
  gap: 6px;
  padding: 0 !important;
  margin-top: 10px !important;
}

/* 按钮样式 */
button[title="详情"], button[aria-label="详情"] {
  background-color: #e3f2fd !important;
  color: #1565c0 !important;
  border: none !important;
}
button[title="详情"]:hover, button[aria-label="详情"]:hover {
  background-color: #bbdefb !important;
}
button[title="编辑"], button[aria-label="编辑"] {
  background-color: #e8f5e9 !important;
  color: #2e7d32 !important;
  border: none !important;
}
button[title="编辑"]:hover, button[aria-label="编辑"]:hover {
  background-color: #c8e6c9 !important;
}
button[title="删除"], button[aria-label="删除"] {
  background-color: #ffebee !important;
  color: #c62828 !important;
  border: none !important;
}
button[title="删除"]:hover, button[aria-label="删除"]:hover {
  background-color: #ffcdd2 !important;
}
</style>
""",
        unsafe_allow_html=True,
    )

    if st.button("新建项目", type="primary"):
        render_create_dialog(repo, service)

    projects_for_dashboard = repo.list()
    render_dashboard(repo, service, projects_for_dashboard)
