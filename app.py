from flask import Flask, render_template, request
from engine import NeuroBalanceEngine  # Importing your logic

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    results = None
    inputs = {}

    if request.method == 'POST':
        try:
            # 1. Get data from HTML form
            principal = float(request.form['principal'])
            rate = float(request.form['rate'])
            years = int(request.form['years'])
            extra = float(request.form.get('extra', 0))

            # 2. Run NeuroBalance Engine
            engine = NeuroBalanceEngine(principal, years, annual_interest_rate=rate)
            df = engine.generate_schedule(extra_payment=extra)

            # 3. Prepare data for the web
            total_interest = df["Interest"].sum()
            months_saved = (years * 12) - len(df)
            
            # Convert DataFrame to a list of dictionaries for HTML
            schedule_data = df.to_dict(orient='records')

            results = {
                "total_interest": f"${total_interest:,.2f}",
                "months_saved": months_saved,
                "actual_months": len(df),
                "schedule": schedule_data
            }
            inputs = {"principal": principal, "rate": rate, "years": years, "extra": extra}

        except ValueError:
            results = {"error": "Invalid input. Please enter numbers only."}

    return render_template('index.html', results=results, inputs=inputs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)