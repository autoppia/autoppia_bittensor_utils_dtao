from colorama import Fore, Style


def color_diff(value: float) -> str:
    diff_str = f"{value:+.9f}"
    if value > 0:
        return f"{Fore.GREEN}{diff_str}{Style.RESET_ALL}"
    elif value < 0:
        return f"{Fore.RED}{diff_str}{Style.RESET_ALL}"
    else:
        return diff_str


def color_value(value: float, decimals: int = 9) -> str:
    value_str = f"{value:.{decimals}f}"
    return f"{Fore.CYAN}{value_str}{Style.RESET_ALL}"
