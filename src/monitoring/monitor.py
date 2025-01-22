from dataclasses import dataclass, field
from typing import Dict

from triggers import PriceAlertTrigger, LowTaoBalanceTrigger, LowAlphaBalanceTrigger
from actions import EmailAction
from src.shared.email_sender import EmailSender
from bittensor.core.chain_data import DynamicInfo


@dataclass
class MonitorData:
    """
    This is the data class your monitor receives each iteration.
    - alpha_balances: e.g., user accounts -> alpha tokens
    - tao_balance: the user's total TAO balance
    - subnets_info: dict of subnet_name -> SubnetInfo
    """
    alpha_balances: Dict[str, float] = field(default_factory=dict)
    tao_balance: float = 0.0
    subnets_info: Dict[str, DynamicInfo] = field(default_factory=dict)
    # Add more fields if needed for other triggers or reporting.


class Monitor:
    """
    Main Monitor class that knows how to gather data and run triggers.
    """

    def __init__(self):
        # Create your email sender and any default actions you want
        email_sender = EmailSender()  # Adjust if your EmailSender needs arguments
        email_action = EmailAction(
            email_sender=email_sender,
            recipients=["example@yourdomain.com"]
        )

        # Example triggers:
        self.triggers = [
            # PriceAlertTrigger: check if alpha_price in a subnet >= threshold
            PriceAlertTrigger(
                price_thresholds={"subnetA": 10.0, "subnetB": 9.0},
                actions=[email_action]
            ),
            # LowTaoBalanceTrigger: checks if user's TAO balance < threshold
            LowTaoBalanceTrigger(
                tao_threshold=50.0,
                actions=[email_action]
            ),
            # LowAlphaBalanceTrigger: checks if alpha balances in any account < threshold
            LowAlphaBalanceTrigger(
                alpha_threshold=5.0,
                actions=[email_action]
            )
        ]

    def get_monitor_data(self) -> MonitorData:
        """
        Fetch or compute the data you need for monitoring.
        For demonstration, we hardcode some values.
        """
        # In real scenarios, you'd pull these from APIs, databases, or on-chain data, etc.
        return MonitorData(
            alpha_balances={
                "account1": 3.2,
                "account2": 12.0,
            },
            tao_balance=45.0,  # Suppose the user’s TAO balance is 45.0
            subnets_info={
                "subnetA": DynamicInfo(price=12.5),
                "subnetB": DynamicInfo(price=8.5),
            }
        )

    def run(self):
        """
        Call this to run the monitoring loop once. It fetches fresh data,
        then passes it to each trigger to evaluate.
        """
        data = self.get_monitor_data()
        for trigger in self.triggers:
            trigger.run(data)


if __name__ == "__main__":
    monitor = Monitor()
    monitor.run()
