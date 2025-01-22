import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

from monitor import MonitorData  # import the MonitorData class
from actions import Action       # import the base Action class (e.g., EmailAction)


class Alert:
    """
    Simple Alert class capturing relevant details. You can customize
    this based on your requirements (severity, etc.).
    """

    def __init__(self, title: str, message: str, details: Dict[str, Any]):
        self.title = title
        self.message = message
        self.details = details
        self.timestamp = time.time()


class Trigger(ABC):
    """
    Base class for all triggers. Each trigger can optionally have one or more
    actions that will be executed if the trigger condition is met.
    """

    def __init__(self, actions: Optional[List[Action]] = None):
        self.actions = actions if actions else []

    @abstractmethod
    def check(self, data: MonitorData) -> Optional[Alert]:
        """
        Evaluate whether this trigger condition is met. If it is,
        return an Alert; otherwise return None.
        """
        pass

    def run(self, data: MonitorData):
        """
        Call `check`. If it returns an Alert, pass it on to the attached actions.
        """
        alert = self.check(data)
        if alert:
            for action in self.actions:
                action.execute(alert)


class PriceAlertTrigger(Trigger):
    """
    Example trigger: checks if any subnet's alpha_price is >= a defined threshold.
    If so, it creates an Alert to be handled by the attached actions (e.g., email).
    """

    def __init__(self, price_thresholds: Dict[str, float], actions: Optional[List[Action]] = None):
        super().__init__(actions)
        self.price_thresholds = price_thresholds

    def check(self, data: MonitorData) -> Optional[Alert]:
        for subnet_name, threshold in self.price_thresholds.items():
            # Each subnet has SubnetInfo; get it from data.subnets_info
            subnet_info = data.subnets_info.get(subnet_name)
            if subnet_info is None:
                continue

            current_price = subnet_info.alpha_price
            if current_price >= threshold:
                return Alert(
                    title="Price Threshold Exceeded",
                    message=f"Subnet '{subnet_name}' price is {current_price:.2f}, exceeding threshold {threshold:.2f}",
                    details={
                        "subnet_name": subnet_name,
                        "current_price": current_price,
                        "threshold": threshold
                    }
                )
        return None


class LowTaoBalanceTrigger(Trigger):
    """
    Checks if the user's TAO balance is below a certain threshold.
    """

    def __init__(self, tao_threshold: float, actions: Optional[List[Action]] = None):
        super().__init__(actions)
        self.tao_threshold = tao_threshold

    def check(self, data: MonitorData) -> Optional[Alert]:
        if data.tao_balance < self.tao_threshold:
            return Alert(
                title="Low TAO Balance",
                message=f"TAO balance {data.tao_balance:.4f} is below threshold {self.tao_threshold:.4f}",
                details={
                    "tao_balance": data.tao_balance,
                    "threshold": self.tao_threshold
                }
            )
        return None


class LowAlphaBalanceTrigger(Trigger):
    """
    Checks if alpha balances in the user's watched accounts are below a certain threshold.
    alpha_balances is a dict: {account_id: balance}, or whichever key system you prefer.
    """

    def __init__(self, alpha_threshold: float, actions: Optional[List[Action]] = None):
        super().__init__(actions)
        self.alpha_threshold = alpha_threshold

    def check(self, data: MonitorData) -> Optional[Alert]:
        for account, balance in data.alpha_balances.items():
            if balance < self.alpha_threshold:
                return Alert(
                    title="Low Alpha Balance",
                    message=f"Account '{account}' alpha balance {balance:.4f} is below threshold {self.alpha_threshold:.4f}",
                    details={
                        "account": account,
                        "alpha_balance": balance,
                        "threshold": self.alpha_threshold
                    }
                )
        return None
