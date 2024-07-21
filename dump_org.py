# pyright: reportUnknownVariableType=false

from boto3 import Session
from org_graph import get_org_graph, save_org_graph


def main() -> None:
    "Write the organization graph to standard output as GraphML."
    org = get_org_graph(Session())
    save_org_graph(org)


if __name__ == "__main__":
    main()
