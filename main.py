import numpy as np
import pandas as pd
from datetime import date

class NeuroBalanceEngine:
    def __init__(self, principal, annual_interest_rate, duration_years=None, duration_months=None, payment_frequency="monthly"):
        """
        Initialize the Liability Input Module.
        
        Args:
            principal (float): The total loan amount.
            annual_interest_rate (float): Annual interest rate (e.g., 5.5 for 5.5%).
            duration_years (int, optional): Total loan term in years.
            duration_months (int, optional): Total loan term in months (alternative to years).
            payment_frequency (str): 'monthly' or 'semi-monthly' (defaults to 'monthly').
        """
        self.principal = principal
        self.annual_rate = annual_interest_rate / 100

        freq = payment_frequency.lower()
        if freq in ("monthly", "month"):
            self.periods_per_year = 12
            self.freq_label = "monthly"
        elif freq in ("semi-monthly", "semimonthly", "semi_monthly", "semi"):
            self.periods_per_year = 24
            self.freq_label = "semi-monthly"
        else:
            raise ValueError("payment_frequency must be 'monthly' or 'semi-monthly'")

        # Determine total number of payment periods
        if duration_months is not None:
            # duration_months is in calendar months; convert to periods
            if self.periods_per_year == 12:
                self.total_periods = int(duration_months)
            else:
                # semi-monthly -> 2 payments per month
                self.total_periods = int(duration_months * (self.periods_per_year / 12))
        elif duration_years is not None:
            self.total_periods = int(duration_years * self.periods_per_year)
        else:
            raise ValueError("Either duration_years or duration_months must be provided")

        # Periodic interest rate based on frequency
        self.period_rate = self.annual_rate / self.periods_per_year
        self.standard_payment = self._calculate_pmt()

    def _calculate_pmt(self):
        """
        Calculates the standard amortization payment per period based on payment frequency.
        Formula: P * (r(1+r)^n) / ((1+r)^n - 1)
        """
        if self.period_rate == 0:
            return self.principal / self.total_periods

        r = self.period_rate
        n = self.total_periods
        numerator = self.principal * r * ((1 + r) ** n)
        denominator = ((1 + r) ** n) - 1
        return numerator / denominator

    def generate_schedule(self, extra_payment=0, one_time_extra=0, one_time_period=None):
        """
        Generates the amortization schedule and simulates payoff timeline.
        Returns a Pandas DataFrame.
        """
        schedule = []
        remaining_balance = self.principal
        period = 1

        # Determine base payment (Standard + Recurring Extra)
        base_payment = self.standard_payment + extra_payment

        while remaining_balance > 0 and period <= (self.total_periods * 4):
            # Interest for this period
            interest_payment = remaining_balance * self.period_rate

            # Add one-time extra if this is the chosen period
            one_time = one_time_extra if (one_time_period is not None and period == one_time_period) else 0

            # Total payment this period includes base recurring plus one-time
            actual_payment = base_payment + one_time

            # Principal reduction
            principal_payment = actual_payment - interest_payment

            # Handle final period adjustment
            if remaining_balance < principal_payment:
                principal_payment = remaining_balance
                actual_payment = interest_payment + principal_payment

            remaining_balance -= principal_payment

            schedule.append({
                "Period": period,
                "Payment": round(actual_payment, 2),
                "Principal Paid": round(principal_payment, 2),
                "Interest Paid": round(interest_payment, 2),
                "Remaining Balance": round(remaining_balance, 2)
            })

            period += 1

        # Convert to DataFrame for analysis
        df = pd.DataFrame(schedule)
        return df

    def run_simulation(self, extra_payment=0, one_time_extra=0, one_time_period=None):
        """
        Runs the simulation and prints the MVP metrics.
        """
        df = self.generate_schedule(extra_payment, one_time_extra, one_time_period)
        total_interest = df["Interest Paid"].sum()
        original_periods = self.total_periods
        actual_periods = len(df)
        # convert saved time to months for readability
        months_saved = (original_periods - actual_periods) * (12 / self.periods_per_year)

        print("\n" + "="*40)
        print(f"🧬 NEUROBALANCE ENGINE REPORT")
        one_time_desc = f" + one-time ${one_time_extra} at period {one_time_period}" if one_time_extra and one_time_period else ""
        print(f"   Strategy: +${extra_payment}/{self.freq_label} Extra Payment{one_time_desc}")
        print("="*40)
        print(f"📉 Original Principal:   ${self.principal:,.2f}")
        print(f"📅 Original Term:        {original_periods} payments ({self.periods_per_year} per year)")
        print(f"🚀 Actual Payoff Time:   {actual_periods} payments")
        print(f"⏱️ Time Saved:           {months_saved:.1f} months")
        print(f"💰 Total Interest Paid:  ${total_interest:,.2f}")
        print("-" * 40)

        # Preview the first 5 periods of decay
        print(f"\n🔍 Balance Decay Preview (First 5 {self.freq_label} Payments):")
        print(df.head().to_string(index=False))
        print("\n" + "="*40 + "\n")

# --- MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    # Example Inputs
    loan_amount = 50000    # $50,000 Liability
    interest_rate = 5.0    # 5.0% APR
    years = 5              # 5 Year Term

    # Initialize Engine (monthly payments, specified in years)
    engine = NeuroBalanceEngine(loan_amount, interest_rate, duration_years=years, payment_frequency="monthly")

    # Simulation 1: Standard Payoff (Baseline)
    engine.run_simulation(extra_payment=0)

    # Simulation 2: Accelerated Payoff (Optimization Strategy)
    engine.run_simulation(extra_payment=200)

    # Simulation 3: One-time lump-sum payment example
    print("\n--- One-time lump-sum example ---\n")
    # Apply a one-time $5,000 payment at the 1st payment
    engine.run_simulation(extra_payment=0, one_time_extra=5000, one_time_period=1)

    # Example: semi-monthly payments with duration provided in months
    print("\n--- Semi-monthly example (duration in months) ---\n")
    engine_semi = NeuroBalanceEngine(loan_amount, interest_rate, duration_months=60, payment_frequency="semi-monthly")
    engine_semi.run_simulation(extra_payment=0)