from flask import Blueprint, request, abort, jsonify, make_response
import json
import datetime

# Make the Snowflake connection
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from snowflake.connector import DictCursor

from spcs_helpers.connection import connection as snow_connection
conn = snow_connection()

# Make the API endpoints
connector = Blueprint('connector', __name__)

dateformat = '%Y-%m-%d'

## Top clerks in date range
@connector.route('/top_clerks')
def top_clerks():
    # Validate arguments
    sdt_str = request.args.get('start_range') or '1995-01-01'
    edt_str = request.args.get('end_range') or '1995-03-31'
    topn_str = request.args.get('topn') or '10'
    try:
        sdt = datetime.datetime.strptime(sdt_str, dateformat)
        edt = datetime.datetime.strptime(edt_str, dateformat)
        topn = int(topn_str)
    except:
        abort(400, "Invalid arguments.")
    sql_string = '''
        SELECT
            o_clerk
          , SUM(o_totalprice) AS clerk_total
        FROM snowflake_sample_data.tpch_sf10.orders
        WHERE o_orderdate >= '{sdt}'
          AND o_orderdate <= '{edt}'
        GROUP BY o_clerk
        ORDER BY clerk_total DESC
        LIMIT {topn}
    '''
    sql = sql_string.format(sdt=sdt, edt=edt, topn=topn)
    try:
        res = conn.cursor(DictCursor).execute(sql)
        return make_response(jsonify(res.fetchall()))
    except:
        abort(500, "Error reading from Snowflake. Check the logs for details.")

## Top 10 customers in date range
@connector.route('/customers/top10')
def customers_top10():
    # Validate arguments
    sdt_str = request.args.get('start_range') or '1995-01-01'
    edt_str = request.args.get('end_range') or '1995-03-31'
    try:
        sdt = datetime.datetime.strptime(sdt_str, dateformat)
        edt = datetime.datetime.strptime(edt_str, dateformat)
    except:
        abort(400, "Invalid start and/or end dates.")
    sql_string = '''
        SELECT
            o_custkey
          , SUM(o_totalprice) AS sum_totalprice
        FROM snowflake_sample_data.tpch_sf10.orders
        WHERE o_orderdate >= '{sdt}'
          AND o_orderdate <= '{edt}'
        GROUP BY o_custkey
        ORDER BY sum_totalprice DESC
        LIMIT 10
    '''
    sql = sql_string.format(sdt=sdt, edt=edt)
    try:
        res = conn.cursor(DictCursor).execute(sql)
        return make_response(jsonify(res.fetchall()))
    except:
        abort(500, "Error reading from Snowflake. Check the logs for details.")

## Monthly sales for a clerk in a year
@connector.route('/clerk/<clerkid>/yearly_sales/<year>')
def clerk_montly_sales(clerkid, year):
    # Validate arguments
    try: 
        year_int = int(year)
    except:
        abort(400, "Invalid year.")
    if not clerkid.isdigit():
        abort(400, "Clerk ID can only contain numbers.")
    clerkid_str = f"Clerk#{clerkid}"
    sql_string = '''
        SELECT
            o_clerk
          ,  Month(o_orderdate) AS month
          , SUM(o_totalprice) AS sum_totalprice
        FROM snowflake_sample_data.tpch_sf10.orders
        WHERE Year(o_orderdate) = {year}
          AND o_clerk = '{clerkid}'
        GROUP BY o_clerk, month
        ORDER BY o_clerk, month
    '''
    sql = sql_string.format(year=year_int, clerkid=clerkid_str)
    try:
        res = conn.cursor(DictCursor).execute(sql)
        return make_response(jsonify(res.fetchall()))
    except:
        abort(500, "Error reading from Snowflake. Check the logs for details.")
