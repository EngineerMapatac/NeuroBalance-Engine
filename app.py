from flask import Flask, render_template, request
from engine import NeuroBalanceEngine

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    results = None
    inputs = {'currency': '₱'}

    if request.method == 'POST':
        try:
            principal = float(request.form['principal'])
            months = int(request.form['months'])
            
            extra_raw = request.form.get('extra')
            extra = float(extra_raw) if extra_raw else 0.00
            
            currency = request.form.get('currency', '₱')
            
            total_payable_raw = request.form.get('total_payable')
            rate_raw = request.form.get('rate')

            if total_payable_raw:
                total_payable = float(total_payable_raw)
                monthly_pmt = total_payable / months
                engine = NeuroBalanceEngine(principal, months, monthly_payment=monthly_pmt)
                rate = round((engine.monthly_rate * 100), 2)
            else:
                rate = float(rate_raw)
                engine = NeuroBalanceEngine(principal, months, monthly_interest_rate=rate)
                total_payable = ""

            df = engine.generate_schedule(extra_payment=extra)

            total_interest = df["Interest"].sum()
            months_saved = months - len(df)
            
            schedule_data = df.to_dict(orient='records')

            results = {
                "total_interest": f"{currency}{total_interest:,.2f}",
                "months_saved": months_saved,
                "actual_months": len(df),
                "schedule": schedule_data,
                "currency": currency
            }
            inputs = {
                "principal": principal, 
                "rate": rate, 
                "months": months, 
                "extra": extra, 
                "currency": currency,
                "total_payable": total_payable
            }

        except ValueError:
            results = {"error": "Invalid input. Please enter numbers only."}

    return render_template('index.html', results=results, inputs=inputs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)