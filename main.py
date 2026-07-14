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

    # Expose backend API to the frontend (pywebview exposes only callable functions)
    try:
        from backend.renamer import RenamerAPI

        api = RenamerAPI()
        window.expose(
            api.api_preview,
            api.api_rename_all,
            api.api_undo_last,
            api.api_pick_folder,
            api.api_pick_topics_file,
        )
    except Exception as e:
        print("Failed to expose API:", e)





    webview.start(debug=False, http_server=False)


if __name__ == "__main__":
    main()

