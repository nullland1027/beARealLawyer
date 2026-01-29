import streamlit as st

from ui.layout import render_app


def main() -> None:
    st.set_page_config(page_title="律师案件管理", layout="wide")
    render_app()


if __name__ == "__main__":
    main()
