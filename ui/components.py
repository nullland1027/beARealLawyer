from __future__ import annotations

from typing import List, Optional

import streamlit as st

from pathlib import Path

from core.file_links import open_local_file
from core.models import Project


def render_metrics(projects: List[Project]) -> None:
    total = len(projects)
    processing = len([item for item in projects if item.status == "正在处理"])
    closed = len([item for item in projects if item.status == "已结案"])
    waiting = len([item for item in projects if item.status == "等待接手"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("全部项目", total)
    col2.metric("正在处理", processing)
    col3.metric("已结案", closed)
    col4.metric("等待接手", waiting)


def render_project_table(projects: List[Project]) -> None:
    table_rows = []
    for item in projects:
        table_rows.append(
            {
                "项目名称": item.name,
                "当事人": item.client,
                "相对人": item.opponent,
                "承办律师": item.lawyer,
                "阶段": item.stage,
                "完成度": f"{item.completion}%",
                "状态": item.status,
                "更新时间": item.updated_at or item.created_at,
            }
        )
    if not table_rows:
        st.info("暂无项目，可以点击上方“新建项目”按钮创建。")
        return
    st.dataframe(table_rows, use_container_width=True, hide_index=True)


def render_project_detail(project: Optional[Project]) -> None:
    if not project:
        st.info("请先选择一个项目查看详情。")
        return

    st.subheader(project.name)
    st.caption(f"项目编号：{project.id}")
    st.write(f"当事人：{project.client}")
    st.write(f"相对人：{project.opponent}")
    st.write(f"承办律师：{project.lawyer}")
    st.write(f"阶段：{project.stage}")
    st.write(f"完成度：{project.completion}%")
    st.write(f"状态：{project.status}")


    if project.notes:
        st.write("备注：")
        st.write(project.notes)

    st.divider()
    st.write("📎 附件（文件和文件夹）")
    if not project.files:
        st.caption("尚未添加文件或文件夹。")
        return

    for index, file in enumerate(project.files):
        col_icon, col_name, col_action = st.columns([0.1, 0.7, 0.2])
        col_icon.write(file.icon())
        col_name.write(file.name)
        if col_action.button("打开", key=f"open_file_{project.id}_{index}"):
            if file.path and Path(file.path).exists():
                if file.is_folder:
                    from core.file_links import open_folder_in_finder
                    open_folder_in_finder(file.path)
                else:
                    open_local_file(file.path)
            else:
                st.warning("路径无效，无法打开。")
        if not file.path:
            col_name.caption("路径为空")
        elif not Path(file.path).exists():
            col_name.caption("路径不存在")
