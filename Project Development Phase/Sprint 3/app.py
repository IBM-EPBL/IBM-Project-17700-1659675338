import sqlite3
from flask import Flask, redirect, url_for, render_template, request, session
import pandas as pd
import numpy as np
import pickle
from sklearn.preprocessing import LabelEncoder
import requests


def register_user_to_db(username,email,contact,password):
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute('INSERT INTO users(username,email,contact,password) values (?,?,?,?)', (username,email,contact,password))
    con.commit()
    con.close()


def check_user(username, password):
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute('Select username,password FROM users WHERE username=? and password=?', (username, password))

    result = cur.fetchone()
    if result:
        return True
    else:
        return False


app = Flask(__name__)
filename = 'resale_model.sav'
model_rand = pickle.load(open(filename, 'rb'))

app.secret_key = "r@nd0mSk_1"


@app.route("/")
def index():
    return render_template('resaleintro.html')


@app.route('/register', methods=["POST", "GET"])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        contact = request.form['contact']
        password = request.form['password']
        

        register_user_to_db(username,email,contact,password)
        return render_template('login.html')
      # return redirect(url_for('index'))

    else:
        
        return render_template('register.html')


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(check_user(username, password))
        if check_user(username, password):
            session['username'] = username
        #return render_template('resalepredict.html')
        return redirect(url_for('predict'))
    else:
      #  return redirect(url_for('index'))
         return render_template('login.html')


@app.route('/predict', methods=['POST', "GET"])
def predict():
    if 'username' in session:
        return render_template('resalepredict.html', username=session['username'])
    else:
        return render_template('login.html',info='Username or Password is wrong!')


@app.route('/y_predict', methods=['GET', 'POST'])
def y_predict():
    regyear = int (request.args.get('regyear'))
    powerps = float(request.args.get('powerps'))
    kms = float(request.args.get('kms'))
    regmonth = int(request.args.get('regmonth'))
    
    
    gearbox = request.args.get('geartype')
    damage = request.args.get('damage')
    model = request.args.get('model') 
    brand= request.args.get('brand')
    fuelType = request.args.get('fuelType') 
    vehicletype= request.args.get('vehicletype')
    new_row={'yearOfRegistration':regyear, 'powerPS':powerps, 'kilometer':kms, 'monthofRegistration': regmonth, 
             'gearbox': gearbox, 'notRepairedDamage': damage,'model':model, 
             'brand':brand, 'fuelType': fuelType,'vehicleType': vehicletype}
    print(new_row)
    new_dataset = pd.DataFrame(columns =['vehicleType', 'yearOfRegistration', 'gearbox', 'powerPS', 'model',
                                    'kilometer', 'monthofRegistration', 'fuelType', 'brand', 'notRepairedDamage'])
    new_dataset= new_dataset.append(new_row, ignore_index = True)
    labels = ['gearbox', 'notRepairedDamage', 'model', 'brand', 'fuelType', 'vehicleType']
    mapper = {}
    for i in labels:
        mapper[i] = LabelEncoder()
        mapper[i].classes = np.load('../IBM carproject/'+str('classes'+i+'.npy'), allow_pickle=True)
        tr = mapper[i].fit_transform(new_dataset[i])
        new_dataset.loc[:,i + '_labels'] = pd.Series(tr, index = new_dataset.index)
    
    labeled = new_dataset[ ['yearOfRegistration','powerPS','kilometer','monthofRegistration']+[x+'_labels' for x in labels]]
    
    X = labeled.values
    print(X)
    
    y_prediction = model_rand.predict(X)
    print(y_prediction)
    return render_template('predict.html', predict='The resale value predicted is {:.2f} $'.format(y_prediction[0]))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)