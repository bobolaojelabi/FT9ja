from flask import Flask, render_template, request, url_for, redirect, flash, session
from pymongo import MongoClient
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plot
import random

#initiate flask app
app = Flask(__name__)
#secret key
app.config["SECRET_KEY"]= "AGHJ24365gvhbvh"

# MongoDB configuration
client = MongoClient('mongodb://localhost:27017/')
db = client['trader']
collection = db['trader_data']

traders = 10 #number of traders
capital = 100 #initial capital
profit_range = (-5,5) #possible profits and losses per minute
duration = 20 #duration 20min


#function to plot graph
def plot_graph(name, profit_data):
    plot.plot(range(len(profit_data)), profit_data)
    plot.xlabel('Minute')
    plot.ylabel('Profit / loss')
    plot.title(f'{name} Profit / loss Over Time')
    plot.grid(True)
    plot.savefig(f'static/graph/{name}.png')
    plot.close()  # Close the plot to free up resources

#index route
@app.route('/')
def index():
    total_trader = collection.count_documents({})
    if total_trader == 0:
        for trader in range(traders):
            trader_name = f"Trader {trader+1}"
            trader_profit = [] #list to store trader's profit
            for min in range(duration):
                random_number = random.uniform(0,1) # generate a random number betweeen 0 and 1
                profit = random_number * (profit_range[1] - profit_range[0]) + profit_range[0] # Map the random number to profit range
                if min == 0:
                    total_profit = capital + profit
                else:
                    total_profit += profit

                new_profit = round(total_profit, 1)  # Round the profit to one decimal place
                trader_profit.append(new_profit)

            #store trader data into Mongodb
            data = {
                "trader_name":trader_name,
                "profit/loss":trader_profit
            }
            collection.insert_one(data)

        return render_template('index.html')
    else:
        return render_template('index.html')


#trader
@app.route('/trader/', methods=['POST', 'GET'])
def trader():
    if request.method == 'POST':
        name = request.form.get('trader_name')
        data = collection.find_one({'trader_name': name})
        if data:
            profit_data = data['profit/loss']
            plot_graph(name, profit_data)
            return render_template('trader.html', name=name, profit_data=profit_data)
        else:
            flash("Trader data not found. Follow the format(Trader 1)", "error")
            return redirect('/')
    else:
        return redirect('/')

#admin login
@app.route('/admin/login/', methods=['POST', 'GET'])
def admin_login():
    if request.method == 'GET':
        return render_template('admin_login.html')
    else:
        email = request.form.get('email')
        pwd = request.form.get('password')
        query = db.admin.find_one({"email":email, "password":pwd})
        if query != None:
            session['admin'] = email
            return redirect(url_for('admin'))
        else:
            flash("Inaklid credentials.", 'error')
            return redirect(url_for('admin_login'))

#admin signout
@app.route('/admin/signout/')
def admin_signout():
    if session.get('admin') != None:
        session.pop('admin', None)
    return redirect('/admin/login/')

#admin
@app.route('/admin/')
def admin():
    if session.get('admin') != None:
        details = []
        trader_deets = collection.find()
        for deets in trader_deets:
            name = deets['trader_name']
            profit_loss = deets['profit/loss'][-1] # to get the current profit/loss
            details.append({
                'name':name,
                'profit':profit_loss
            })

        return render_template('admin.html', details=details)
    else:
        return redirect('/admin/login/')

#admin trader_info
@app.route('/trader_info/<name>')
def trader_info(name):
        if session.get('admin') != None:
            data = collection.find_one({'trader_name': name})
            if data:
                profit_data = data['profit/loss']
                plot_graph(name, profit_data)
                return render_template('trader_info.html', name=name, profit_data=profit_data)
            else:
                return redirect('/admin/login/')
   


if __name__ == "__main__":
    app.run(debug=True)

