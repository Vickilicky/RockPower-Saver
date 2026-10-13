# RockPower: Solar for Township Businesses and Youth

Built by **Rooted Upon The Rock Solar Installation, Soweto** for the FNB Hackathon and the FNB App of the Year awards.

## The problem

In townships like Soweto, load shedding and expensive generator fuel hurt two groups:

- **Small businesses** (spaza shops, salons, chisanyamas, butcheries, car washes) lose trading hours and money when the power goes off.
- **Young people** lose safe, affordable places to play games, hear music and watch movies when venues go dark, and have few entry points into the green economy.

## Our solution: one app, five steps

RockPower walks a business from "what am I losing?" to "I have solar", and gives young people jobs and powered spaces along the way.

1. **Audit:** a 60-second check shows what a business loses each month to wasted energy and generator costs.
2. **Quote:** pick the appliances you run and get panels, battery size, price, a 24-month plan and the monthly saving. Share the quote on WhatsApp.
3. **Kits & Jobs:** apply for a pay-as-you-save kit and hire a local young installer, so every install is a township job.
4. **Power:** book time at township solar hubs for businesses and youth venues. Capacity is checked per time slot, and green points reward daytime solar use.
5. **Impact:** a dashboard built from real use of the app: businesses audited, savings found, quotes, kit applications, installer requests, bookings and customers.

One customer is linked by phone number across kits, jobs, bookings and points.

## How it helps

- **Cuts costs** by showing each business what it loses and what solar could save.
- **Keeps power on** through solar kits and hubs during outages.
- **Creates jobs** by using local young installers.
- **Rewards good habits** with green points for daytime solar use.

## Run it

**Python (Flask)**

```
pip install flask
python rockpower_combined.py
```

Open http://127.0.0.1:5000. Data is saved in `rockpower_combined.db`.

**Web (no install)**

Open `rockpower_combined.html` in any browser. Data is saved in the browser.

Live demo: `https://YOURUSERNAME.github.io/YOUR-REPO/`

## Files

- `rockpower_combined.py`: the full app in Python (Flask and SQLite)
- `rockpower_combined.html`: the same app as a single web page
- `index.html`: landing page that opens the app
- `solarspot`, `kasiwatts`, `rockpower` (.py and .html): the three earlier apps that were combined into this one. KasiWatts needs `pip install flask sqlalchemy`.

## What is real and what is placeholder

- **Prices and rates** (panels, batteries, tariffs, generator cost per hour, kit prices) are placeholders at the top of each file. They need to be replaced with our real figures.
- **Waste and saving percentages** in the audit are estimates. A site visit gives the real figure.
- **Solar hubs** are sample data for the demo. The installers listed are real.
- **The dashboard** shows counts from real use of the app. It starts at zero.

## Next steps

- Payments through FNB eWallet or pay-to-cell
- Verified installer profiles and ratings
- Real-time energy readings from installed systems
- An admin screen to update hub status
- Saved customer records and installer follow-up

## Contact

Victoria Nkhoma  
27627873997  
s_nkhoma@yahoo.com
