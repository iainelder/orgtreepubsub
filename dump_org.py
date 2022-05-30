from boto3 import Session
from org_graph import get_org_graph, write_graphml


def main() -> None:
    "Write the organization graph to standard output as GraphML."
    org = get_org_graph(Session())
    write_graphml(org)


if __name__ == "__main__":
    main()
