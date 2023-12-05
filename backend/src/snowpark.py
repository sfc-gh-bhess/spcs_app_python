from flask import Blueprint, request, abort, make_response, jsonify
import datetime
import snowflake.snowpark.functions as f

from spcs_helpers.connection import session as snow_session
session = snow_session()

# Make the API endpoints
snowpark = Blueprint('snowpark', __name__)

dateformat = '%Y-%m-%d'

## Top clerks in date range
@snowpark.route('/top_clerks')
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
    try:
        df = session.table('snowflake_sample_data.tpch_sf10.orders') \
                .filter(f.col('O_ORDERDATE') >= sdt) \
                .filter(f.col('O_ORDERDATE') <= edt) \
                .group_by(f.col('O_CLERK')) \
                .agg(f.sum(f.col('O_TOTALPRICE')).as_('CLERK_TOTAL')) \
                .order_by(f.col('CLERK_TOTAL').desc()) \
                .limit(topn)
        return make_response(jsonify([x.as_dict() for x in df.to_local_iterator()]))
    except:
        abort(500, "Error reading from Snowflake. Check the logs for details.")

## Top 10 customers in date range
@snowpark.route('/customers/top10')
def customers_top10():
    # Validate arguments
    sdt_str = request.args.get('start_range') or '1995-01-01'
    edt_str = request.args.get('end_range') or '1995-03-31'
    try:
        sdt = datetime.datetime.strptime(sdt_str, dateformat)
        edt = datetime.datetime.strptime(edt_str, dateformat)
    except:
        abort(400, "Invalid start and/or end dates.")
    try:
        df = session.table('snowflake_sample_data.tpch_sf10.orders') \
                .filter((f.col('O_ORDERDATE') >= sdt) & (f.col('O_ORDERDATE') <= edt)) \
                .group_by(f.col('O_CUSTKEY')) \
                .agg(f.sum(f.col('O_TOTALPRICE')).alias('SUM_TOTALPRICE')) \
                .sort(f.col('SUM_TOTALPRICE').desc()) \
                .limit(10)
        return make_response(jsonify([x.as_dict() for x in df.to_local_iterator()]))
    except:
        abort(500, "Error reading from Snowflake. Check the logs for details.")

## Monthly sales for a clerk in a year
@snowpark.route('/clerk/<clerkid>/yearly_sales/<year>')
def clerk_montly_sales(clerkid, year):
    # Validate arguments
    try: 
        year_int = int(year)
    except:
        abort(400, "Invalid year.")
    if not clerkid.isdigit():
        abort(400, "Clerk ID can only contain numbers.")
    clerkid_str = f"Clerk#{clerkid}"
    try:
        df = session.table('snowflake_sample_data.tpch_sf10.orders') \
                .filter(f.year(f.col('O_ORDERDATE')) == year_int) \
                .filter(f.col('O_CLERK') == clerkid_str) \
                .with_column('MONTH', f.month(f.col('O_ORDERDATE'))) \
                .groupBy(f.col('O_CLERK'), f.col('MONTH')) \
                .agg(f.sum(f.col('O_TOTALPRICE')).alias('SUM_TOTALPRICE')) \
                .sort(f.col('O_CLERK'), f.col('MONTH'))
        return make_response(jsonify([x.as_dict() for x in df.to_local_iterator()]))
    except:
        abort(500, "Error reading from Snowflake. Check the logs for details.")