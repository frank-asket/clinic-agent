"""Save the clinic booking LangGraph flow to PNG in this folder."""

from pathlib import Path
import sys

AGENTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = AGENTS_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.booking_agent import booking_graph  # noqa: E402


def save_graph_files() -> None:
    """Export graph as PNG."""
    graph = booking_graph.get_graph()
    png_path = AGENTS_DIR / "langgraph_flow.png"
    try:
        png_data = graph.draw_mermaid_png()
        png_path.write_bytes(png_data)
        print(f"Saved PNG flow to: {png_path}")
    except Exception as exc:
        print(
            "Could not render PNG (install Graphviz on your system). "
            f"Error: {exc}\n"
            "On macOS: brew install graphviz"
        )


if __name__ == "__main__":
    save_graph_files()
