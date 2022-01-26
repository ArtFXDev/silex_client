import sys
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f', help="file path", type= str)
    args = parser.parse_args()
    file=args.file


    hou.hipFile.load(file)
    render_nodes=[rn.name() for rn in hou.node('/out').allSubChildren()]
    print(render_nodes)


if __name__ == "__main__":
    main()