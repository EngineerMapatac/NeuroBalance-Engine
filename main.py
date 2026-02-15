import numpy as np
import pandas as pd
from datetime import date

class NeuroBalanceEngine:
    def __init__(self, principal, annual_interest_rate, duration_years):
        """
        Initialize the Liability Input Module.
        
        Args:
            principal (float): The total loan amount.
            annual_interest_rate (float): Annual interest rate (e.g., 5.5 for 5.5%).
            duration_years (int): Total loan term in years.
        """
        self.principal = principal
        self.annual_rate = annual_interest_rate / 100
        self.monthly_rate = self.annual_rate / 12
        self.total_months = duration_years * 12
        self.standard_payment = self._calculate_pmt()

    def _calculate_pmt(self):
        """
        Calculates the standard monthly amortization payment.
        Formula: P * (r(1+r)^n) / ((1+r)^n - 1)
        """
        if self.monthly_rate == 0:
            return self.principal / self.total_months
        
        numerator = self.principal * self.monthly_rate * ((1 + self.monthly_rate) ** self.total_months)
        denominator = ((1 + self.monthly_rate) ** self.total_months) - 1
        return numerator / denominator

    def generate_schedule(self, extra_payment=0):
        """
        Generates the amortization schedule and simulates payoff timeline.
        Returns a Pandas DataFrame.
        """
        schedule = []
        remaining_balance = self.principal
        month = 1
        
        # Determine actual payment (Standard + Extra Strategy)
        actual_payment = self.standard_payment + extra_payment

        while remaining_balance > 0:
            # Interest Inference for this period
            interest_payment = remaining_balance * self.monthly_rate
            
            # Principal reduction
            principal_payment = actual_payment - interest_payment
            
            # Handle final month adjustment
            if remaining_balance < principal_payment:
                principal_payment = remaining_balance
                actual_payment = interest_payment + principal_payment
            
            remaining_balance -= principal_payment
            
            schedule.append({
                "Month": month,
                "Payment": round(actual_payment, 2),
                "Principal Paid": round(principal_payment, 2),
                "Interest Paid": round(interest_payment, 2),
                "Remaining Balance": round(remaining_balance, 2)
            })
            
            month += 1
            
            # Hard stop safety to prevent infinite loops in edge cases
            if month > (self.total_months * 2): 
                break

        # Convert to DataFrame for analysis
        df = pd.DataFrame(schedule)
        return df

    def run_simulation(self, extra_payment=0):
        """
        Runs the simulation and prints the MVP metrics.
        """
        df = self.generate_schedule(extra_payment)
        
        total_interest = df["Interest Paid"].sum()
        months_saved = self.total_months - len(df)
        
        print("\n" + "="*40)
        print(f"🧬 NEUROBALANCE ENGINE REPORT")
        print(f"   Strategy: +${extra_payment}/mo Extra Payment")
        print("="*40)
        print(f"📉 Original Principal:   ${self.principal:,.2f}")
        print(f"📅 Original Term:        {self.total_months} months")
        print(f"🚀 Actual Payoff Time:   {len(df)} months")
        print(f"⏱️ Time Saved:           {months_saved} months")
        print(f"💰 Total Interest Paid:  ${total_interest:,.2f}")
        print("-" * 40)
        
        # Preview the first 5 months of decay
        print("\n🔍 Balance Decay Preview (First 5 Months):")
        print(df.head().to_string(index=False))
        print("\n" + "="*40 + "\n")

# --- MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    # Example Inputs
    loan_amount = 50000    # $50,000 Liability
    interest_rate = 5.0    # 5.0% APR
    years = 5              # 5 Year Term

    # Initialize Engine
    engine = NeuroBalanceEngine(loan_amount, interest_rate, years)

    # Simulation 1: Standard Payoff (Baseline)
    engine.run_simulation(extra_payment=0)

    # Simulation 2: Accelerated Payoff (Optimization Strategy)
    engine.run_simulation(extra_payment=200)