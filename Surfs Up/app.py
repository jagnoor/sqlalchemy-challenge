import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine 
from sqlalchemy import func

from flask import Flask, jsonify

import datetime as dt 

###############################
# Database Setup
###############################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

#reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to the tables
Measurement = Base.classes.measurement
Station = Base.classes.station

#Create session
session = Session(engine)

#####################
#Flask Setup
#####################
app = Flask(__name__)

# This function called `calc_temps` will accept start date and end date in the format '%Y-%m-%d' 
# and return the minimum, average, and maximum temperatures for that range of dates
def calc_temps(start_date, end_date):
    """TMIN, TAVG, and TMAX for a list of dates.
    
    Args:
        start_date (string): A date string in the format %Y-%m-%d
        end_date (string): A date string in the format %Y-%m-%d
        
    Returns:
        TMIN, TAVE, and TMAX
    """
    
    return session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()

######################
#Flask Routes
######################

@app.route("/")
def main():
    """List all available routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end>"
    )

#Route to precipitation
@app.route("/api/v1.0/precipitation")
def precipitation():

    """Return the JSON representation of your dictionary."""
    print("Received Precipitation api request.")
    
    #Query dates
    final_date_query = session.query(func.max(func.strftime("%Y-%m-%d", Measurement.date))).all()
    max_date_string = final_date_query[0][0]
    max_date = dt.datetime.strptime(max_date_string, "%Y-%m-%d")

    begin_date = max_date - dt.timedelta(365)

    precipitation_data = session.query(func.strftime("%Y-%m-%d", Measurement.date), Measurement.prcp).\
        filter(func.strftime("%Y-%m-%d", Measurement.date) >= begin_date).all()
    
    results_dict = {}
    for result in precipitation_data:
        results_dict[result[0]] = result[1]
    
    return jsonify(results_dict)

#Route to stations
@app.route("/api/v1.0/stations")
def stations():

    """Return a JSON list of stations from the dataset."""
    
    print("Received station api request.")

    stations = session.query(Station).all()
    
    # Create a dictionary from the row data and append to a list of stations_list
    stations_list = []
    for station in stations:
        station_dict = {}
        station_dict["id"] = station.id
        station_dict["station"] = station.station
        station_dict["name"] = station.name
        station_dict["latitude"] = station.latitude
        station_dict["longitude"] = station.longitude
        station_dict["elevation"] = station.elevation
        stations_list.append(station_dict)
    
    return jsonify(stations_list)

#Route to tobs (Temperature Observations)
@app.route("/api/v1.0/tobs")
def tobs():

    """Return a JSON list of temperature observations for the previous year."""
    
    print("Received tobs api request.")

    #Query the dates and temperature observations of the most active station for the last year of data.
    final_date_query = session.query(func.max(func.strftime("%Y-%m-%d", Measurement.date))).all()
    max_date_string = final_date_query[0][0]
    max_date = dt.datetime.strptime(max_date_string, "%Y-%m-%d")

    begin_date = max_date - dt.timedelta(365)

    results = session.query(Measurement).\
        filter(func.strftime("%Y-%m-%d", Measurement.date) >= begin_date).all()
    
    # Create a dictionary from the row data and append to a list of tobs_list
    tobs_list = []
    for result in results:
        tobs_dict = {}
        tobs_dict["date"] = result.date
        tobs_dict["station"] = result.station
        tobs_dict["tobs"] = result.tobs
        tobs_list.append(tobs_dict)
    
    return jsonify(tobs_list)
# Route to <start>
@app.route("/api/v1.0/<start>")
def start(start):

    print("Received start date api request.")

    final_date_query = session.query(func.max(func.strftime("%Y-%m-%d", Measurement.date))).all()
    max_date = final_date_query[0][0]

    #add temperatures
    temps = calc_temps(start, max_date)

    #create list
    return_list = []
    date_dict = {'start_date': start, 'end_date': max_date}
    return_list.append(date_dict)
    return_list.append({'Observation': 'TMIN', 'Temperature': temps[0][1]})
    return_list.append({'Observation': 'TAVG', 'Temperature': temps[0][1]})
    return_list.append({'Observation': 'TMAX', 'Temperature': temps[0][0]})

    return jsonify(return_list)
# Route to <start>/<end>
@app.route("/api/v1.0/<start>/<end>")
def start_end(start, end):
    """Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start or start-end range."""

    print("Received start date and end date api request.")

    #add temperatures
    temps = calc_temps(start, end)

    #create list
    return_list = []
    date_dict = {'start_date': start, 'end_date': end}
    return_list.append(date_dict)
    return_list.append({'Observation': 'TMIN', 'Temperature': temps[0][1]})
    return_list.append({'Observation': 'TAVG', 'Temperature': temps[0][1]})
    return_list.append({'Observation': 'TMAX', 'Temperature': temps[0][0]})

    return jsonify(return_list)

if __name__ == '__main__':
    app.run(debug=True)