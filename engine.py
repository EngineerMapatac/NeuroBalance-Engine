import numpy as np
import pandas as pd
from scipy.optimize import newton

class NeuroBalanceEngine:
    def __init__(self, principal, duration_months, monthly_interest_rate=None, monthly_payment=None):
        self.principal = principal
        self.total_months = int(duration_months)
        
        if monthly_interest_rate is None and monthly_payment is not None:
            self.monthly_rate = self._infer_interest_rate(monthly_payment)
        else:
            self.monthly_rate = monthly_interest_rate / 100.0000

        self.standard_payment = self._calculate_pmt()

    def _calculate_pmt(self):
        if self.monthly_rate == 0: return self.principal / self.total_months
        numerator = self.principal * self.monthly_rate * ((1 + self.monthly_rate) ** self.total_months)
        denominator = ((1 + self.monthly_rate) ** self.total_months) - 1
        return numerator / denominator

    def _infer_interest_rate(self, target_payment):
        low, high = 0.0000, 1.0000
        tolerance = 1e-6
        for _ in range(100):
            mid = (low + high) / 2
            monthly_r = mid
            numerator = self.principal * monthly_r * ((1 + monthly_r) ** self.total_months)
            denominator = ((1 + monthly_r) ** self.total_months) - 1
            guessed_pmt = numerator / denominator
            
            if abs(guessed_pmt - target_payment) < tolerance:
                return mid
            elif guessed_pmt < target_payment:
                low = mid
            else:
                high = mid
        return (low + high) / 2

    def generate_schedule(self, extra_payment=0):
        schedule = []
        remaining_balance = self.principal
        month = 0
        actual_payment = self.standard_payment + extra_payment

        while remaining_balance > 0.01:
            month += 1
            interest_charge = remaining_balance * self.monthly_rate
            principal_paid = actual_payment - interest_charge
            
            if remaining_balance < principal_paid:
                principal_paid = remaining_balance
                actual_payment = interest_charge + principal_paid
            
            remaining_balance -= principal_paid
            
            schedule.append({
                "Month": month,
                "Total Payment": round(actual_payment, 4),
                "Principal": round(principal_paid, 4),
                "Interest": round(interest_charge, 4),
                "Balance": round(remaining_balance, 4)
            })
            
            if month > (self.total_months * 3): break

        return pd.DataFrame(schedule)