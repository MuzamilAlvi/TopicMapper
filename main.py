import os
import webview


def main() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(base_dir, "frontend", "index.html")
    index_url = "file:///" + index_path.replace("\\", "/")

    window = webview.create_window(
        title="TopicMapper – Intelligent Batch Video File Renaming System",

        url=index_url,
        width=1200,
        height=800,
        resizable=True,
    )

    # Expose backend API to the frontend
    try:
        from backend.renamer import RenamerAPI

        api = RenamerAPI()
        # pywebview requires expose() with a callable or a dict of callables.
        window.expose(api.api_preview)
        window.expose(api.api_rename_all)
        window.expose(api.api_undo_last)
    except Exception as e:
        print("Failed to expose API:", e)


    webview.start(debug=False, http_server=False)


if __name__ == "__main__":
    main()

