import numpy as np
import pandas as pd

class NeuroBalanceEngine:
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

    def _calculate_pmt(self):
        """Calculates standard amortization payment."""
        if self.monthly_rate == 0: return self.principal / self.total_months
        
        numerator = self.principal * self.monthly_rate * ((1 + self.monthly_rate) ** self.total_months)
        denominator = ((1 + self.monthly_rate) ** self.total_months) - 1
        return numerator / denominator

    def _infer_interest_rate(self, target_payment):
        """
        INTEREST INFERENCE ENGINE
        Uses binary search to find the rate that matches the target payment.
        """
        low, high = 0.0001, 1.0  # Search range: 0.01% to 100% interest
        tolerance = 1e-6
        
        for _ in range(100):  # Max 100 iterations
            mid = (low + high) / 2
            monthly_r = mid / 12
            
            # Amortization formula with guessed rate
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
        """Generates the amortization schedule DataFrame."""
        schedule = []
        remaining_balance = self.principal
        month = 0
        
        actual_payment = self.standard_payment + extra_payment

        while remaining_balance > 0.01:
            month += 1
            interest_charge = remaining_balance * self.monthly_rate
            principal_paid = actual_payment - interest_charge
            
            # Handle payoff
            if remaining_balance < principal_paid:
                principal_paid = remaining_balance
                actual_payment = interest_charge + principal_paid
            
            remaining_balance -= principal_paid
            
            schedule.append({
                "Month": month,
                "Total Payment": round(actual_payment, 2),
                "Principal": round(principal_paid, 2),
                "Interest": round(interest_charge, 2),
                "Balance": round(remaining_balance, 2)
            })
            
            if month > (self.total_months * 3): break # Safety break

        return pd.DataFrame(schedule)

    def print_report(self, extra_payment=0):
        """Prints a summary report."""
        df = self.generate_schedule(extra_payment)
        total_interest = df["Interest"].sum()
        original_timeline = self.total_months
        actual_timeline = len(df)
        
        print("\n" + "="*50)
        print(f"🧬 NEUROBALANCE REPORT | Extra Pay: ${extra_payment}")
        print("="*50)
        print(f"💰 Principal:       ${self.principal:,.2f}")
        print(f"📉 Annual Rate:     {self.annual_rate * 100:.2f}%")
        print(f"🗓  Original Term:   {original_timeline} months")
        print(f"🚀 Actual Term:     {actual_timeline} months (Saved {original_timeline - actual_timeline} mos)")
        print(f"💵 Total Interest:  ${total_interest:,.2f}")
        print("-" * 50)

# --- EXECUTION ---
if __name__ == "__main__":
    # Case 1: Standard Calculation
    print("\n--- CASE 1: Standard Input ---")
    engine = NeuroBalanceEngine(principal=50000, duration_years=5, annual_interest_rate=5.0)
    engine.print_report(extra_payment=200)

    # Case 2: Interest Inference (Unknown Rate)
    # Scenario: You borrowed $10k for 3 years and pay $304.22/mo. What is the rate?
    print("\n--- CASE 2: Interest Inference (AI Mode) ---")
    engine_inference = NeuroBalanceEngine(principal=10000, duration_years=3, monthly_payment=304.22)
    engine_inference.print_report()
