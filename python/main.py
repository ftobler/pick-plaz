
import os


if __name__ == "__main__":
    from state import main
    main(os.name == "nt")  #if running on windows initialize as mock