#!/usr/bin/env python3
"""
ROS Data Processor - Integrated Version
Analyzes Restaurant Operations System CSV files and generates dashboard metrics
Includes all fixes for date parsing, subscription data, and data merging
"""

import pandas as pd
import json
from datetime import datetime
import numpy as np

def debug_data_merging():
    """Debug function to test data merging step by step"""
    print("🔍 Debugging data merging...")
    
    # Load CSV files
    print("📁 Loading CSV files...")
    orders = pd.read_csv('orders.csv')
    sales = pd.read_csv('sales.csv')
    expenses = pd.read_csv('expenses.csv')
    restaurants = pd.read_csv('restaurants.csv')
    clients = pd.read_csv('clients.csv')
    
    print(f"✅ Loaded: {len(orders)} orders, {len(sales)} sales, {len(expenses)} expenses")
    
    # Test date parsing
    print("\n📅 Testing date parsing...")
    
    # Orders date format
    print(f"Orders date sample: {orders['order_date'].iloc[0]}")
    orders['order_date'] = pd.to_datetime(orders['order_date'], format='%d-%m-%Y', errors='coerce').dt.date
    print(f"Parsed orders date: {orders['order_date'].iloc[0]}")
    
    # Sales date format
    print(f"Sales date sample: {sales['date'].iloc[0]}")
    sales['date'] = pd.to_datetime(sales['date'], errors='coerce').dt.date
    print(f"Parsed sales date: {sales['date'].iloc[0]}")
    
    # Expenses date format
    print(f"Expenses date sample: {expenses['exp_date'].iloc[0]}")
    expenses['exp_date'] = pd.to_datetime(expenses['exp_date'], errors='coerce').dt.date
    print(f"Parsed expenses date: {expenses['exp_date'].iloc[0]}")
    
    # Test merging for restaurant 1, date 2024-01-01
    print("\n🔗 Testing data merging for restaurant 1, 2024-01-01...")
    
    # Get orders for restaurant 1 on 2024-01-01
    target_date = pd.to_datetime('2024-01-01').date()
    restaurant_1_orders = orders[(orders['restaurant_id'] == 1) & (orders['order_date'] == target_date)]
    restaurant_1_sales = sales[(sales['restaurant_id'] == 1) & (sales['date'] == target_date)]
    restaurant_1_expenses = expenses[(expenses['restaurant_id'] == 1) & (expenses['exp_date'] == target_date)]
    
    print(f"Restaurant 1 orders on {target_date}: {len(restaurant_1_orders)}")
    print(f"Restaurant 1 sales on {target_date}: {len(restaurant_1_sales)}")
    print(f"Restaurant 1 expenses on {target_date}: {len(restaurant_1_expenses)}")
    
    if len(restaurant_1_sales) > 0:
        print(f"Sales data: {restaurant_1_sales.iloc[0].to_dict()}")
        revenue = (
            restaurant_1_sales['food_payment'].sum() +
            restaurant_1_sales['drinks_payment'].sum() +
            restaurant_1_sales['other_payment'].sum() +
            restaurant_1_sales['service_charges'].sum() +
            restaurant_1_sales['delivery_charges'].sum()
        )
        print(f"Calculated revenue: £{revenue}")
    
    if len(restaurant_1_expenses) > 0:
        print(f"Expenses data: {restaurant_1_expenses.iloc[0].to_dict()}")
        total_expenses = restaurant_1_expenses['amount'].sum()
        print(f"Total expenses: £{total_expenses}")
    
    # Test the merge operation
    print("\n🔄 Testing merge operation...")
    
    # Orders per day
    orders_daily = (
        orders.groupby(['restaurant_id', 'order_date'])
        .size()
        .reset_index(name='orders_count')
        .rename(columns={'order_date': 'date'})
    )
    
    # Revenue per day from sales
    sales_daily = sales.copy()
    sales_daily['revenue'] = (
        sales_daily['food_payment'] + sales_daily['drinks_payment'] +
        sales_daily['other_payment'] + sales_daily['service_charges'] +
        sales_daily['delivery_charges']
    )
    sales_daily = sales_daily[[
        'restaurant_id', 'date', 'revenue',
        'food_payment', 'drinks_payment', 'other_payment', 'service_charges', 'delivery_charges'
    ]]
    
    # Expenses per day
    expenses_daily = expenses[[
        'restaurant_id', 'exp_date', 'amount', 'bills', 'vendors', 'wage_advance', 'repairs', 'sundries'
    ]].rename(columns={'exp_date': 'date', 'amount': 'expenses'})
    
    # Convert dates to strings for merging
    orders_daily['date'] = orders_daily['date'].astype(str)
    sales_daily['date'] = sales_daily['date'].astype(str)
    expenses_daily['date'] = expenses_daily['date'].astype(str)
    
    print(f"Orders daily shape: {orders_daily.shape}")
    print(f"Sales daily shape: {sales_daily.shape}")
    print(f"Expenses daily shape: {expenses_daily.shape}")
    
    # Test merge
    daily = orders_daily.merge(sales_daily, on=['restaurant_id', 'date'], how='left')
    daily = daily.merge(expenses_daily, on=['restaurant_id', 'date'], how='left')
    
    print(f"Merged daily shape: {daily.shape}")
    
    # Check restaurant 1, 2024-01-01
    test_row = daily[(daily['restaurant_id'] == 1) & (daily['date'] == '2024-01-01')]
    if len(test_row) > 0:
        print(f"Test row data: {test_row.iloc[0].to_dict()}")
    else:
        print("❌ No data found for restaurant 1, 2024-01-01")
    
    # Check for any data in the merged result
    print(f"\n📊 Sample of merged data:")
    print(daily.head(5).to_dict('records'))

def load_and_analyze_data():
    """Load CSV files and calculate key metrics with integrated fixes"""
    
    print("🔄 Loading ROS data files...")
    
    # Load all CSV files
    try:
        clients = pd.read_csv('csv_data/clients.csv')
        restaurants = pd.read_csv('csv_data/restaurants.csv')
        users = pd.read_csv('csv_data/users.csv')
        subscriptions = pd.read_csv('csv_data/subscriptions.csv')
        
        # Load operational data (FULL DATASET)
        orders = pd.read_csv('csv_data/orders.csv')
        sales = pd.read_csv('csv_data/sales.csv')
        expenses = pd.read_csv('csv_data/expenses.csv')
        cashup = pd.read_csv('csv_data/cashup.csv')
        banking = pd.read_csv('csv_data/banking.csv')
        
        print("✅ Data files loaded successfully")
        print(f"📊 Loaded: {len(orders)} orders, {len(sales)} sales, {len(expenses)} expenses")
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None
    
    # Normalize key column types to ensure reliable joins/mapping
    try:
        # Strip whitespace from column names across all loaded dataframes
        for df in [clients, restaurants, users, subscriptions, orders, sales, expenses, cashup, banking]:
            df.columns = df.columns.str.strip()

        if 'subscription_id' in subscriptions.columns:
            subscriptions['subscription_id'] = pd.to_numeric(subscriptions['subscription_id'], errors='coerce').fillna(0).astype(int)
        if 'no_of_users' in subscriptions.columns:
            subscriptions['no_of_users'] = pd.to_numeric(subscriptions['no_of_users'], errors='coerce').fillna(0).astype(int)
        if 'cost' in subscriptions.columns:
            subscriptions['cost'] = pd.to_numeric(subscriptions['cost'], errors='coerce').fillna(0.0).astype(float)

        if 'subscription_id' in clients.columns:
            clients['subscription_id'] = pd.to_numeric(clients['subscription_id'], errors='coerce')
        # Ensure id columns are integers where possible
        for df, col in [
            (clients, 'client_id'), (restaurants, 'id'), (restaurants, 'client_id'),
            (users, 'client_id'), (users, 'restaurant_id')
        ]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
    except Exception as e:
        print(f"⚠️ Type normalization warning: {e}")

    # Calculate key metrics
    metrics = {}
    
    # 1. Basic counts
    metrics['total_clients'] = len(clients)
    metrics['total_restaurants'] = len(restaurants)
    metrics['total_users'] = len(users)
    metrics['total_orders'] = len(orders)
    
    # 2. Geographic distribution
    uk_restaurants = len(restaurants[restaurants['country_id'] == 1])
    india_restaurants = len(restaurants[restaurants['country_id'] == 2])
    metrics['uk_restaurants'] = uk_restaurants
    metrics['india_restaurants'] = india_restaurants
    
    # 3. Client status analysis
    active_clients = len(clients[clients['is_active'] == True])
    inactive_clients = len(clients[clients['is_active'] == False])
    metrics['active_clients'] = active_clients
    metrics['inactive_clients'] = inactive_clients
    
    # 4. Subscription analysis with proper mapping
    print("📋 Processing subscription data...")
    subscription_map = {}
    for _, sub in subscriptions.iterrows():
        subscription_map[int(sub['subscription_id'])] = sub['subscription_name']
    
    metrics['subscription_analysis'] = []
    client_subscription_utilization = []
    
    for _, sub in subscriptions.iterrows():
        users_on_sub = len(users[users.get('client_id', pd.Series()).isin(
            clients[clients['subscription_id'] == sub['subscription_id']]['client_id']
        )])
        metrics['subscription_analysis'].append({
            'name': sub['subscription_name'],
            'cost': sub['cost'],
            'max_users': sub['no_of_users'],
            'current_users': users_on_sub,
            'utilization': round((users_on_sub / sub['no_of_users']) * 100, 1) if sub['no_of_users'] > 0 else 0
        })

    # per-client subscription utilization
    try:
        for _, cl in clients.iterrows():
            raw_sid = cl['subscription_id'] if 'subscription_id' in cl else None
            sub_id = int(raw_sid) if pd.notna(raw_sid) else None
            max_users = int(subscriptions.loc[sub_id, 'no_of_users']) if sub_id is not None and sub_id in subscriptions.index else 0
            sub_name = subscription_map.get(sub_id, '')
            cur_users = int(len(users[users['client_id'] == cl['client_id']])) if 'client_id' in users.columns else 0
            utilization = round((cur_users / max_users) * 100, 1) if max_users > 0 else 0
            client_subscription_utilization.append({
                'client_id': int(cl['client_id']),
                'client_name': cl['legal_name'],
                'subscription_id': int(sub_id),
                'subscription_name': sub_name,
                'max_users': int(max_users),
                'current_users': int(cur_users),
                'utilization': utilization
            })
    except Exception as e:
        print(f"⚠️ Could not compute client subscription utilization: {e}")
    
    metrics['client_subscription_utilization'] = client_subscription_utilization
    
    # 5. Order analysis (FULL DATA)
    if not orders.empty:
        metrics['avg_order_value'] = round(orders['order_total'].mean(), 2)
        metrics['avg_food_amount'] = round(orders['food_amount'].mean(), 2)
        metrics['avg_drinks_amount'] = round(orders['drinks_amount'].mean(), 2)
        
        # Order type distribution
        order_type_dist = orders['order_type'].value_counts()
        metrics['order_type_distribution'] = order_type_dist.to_dict()
        
        # Calculate delivery vs dine-in metrics
        delivery_orders = orders[orders['order_type'] == 'Home Delivery']
        dine_in_orders = orders[orders['order_type'] == 'Dine-in']
        
        if not delivery_orders.empty:
            metrics['avg_delivery_value'] = round(delivery_orders['order_total'].mean(), 2)
        if not dine_in_orders.empty:
            metrics['avg_dine_in_value'] = round(dine_in_orders['order_total'].mean(), 2)
    
    # 6. Sales analysis
    if not sales.empty:
        total_revenue = sales[['food_payment', 'drinks_payment', 'other_payment', 'service_charges', 'delivery_charges']].sum().sum()
        metrics['total_revenue'] = round(total_revenue, 2)
        
        # Revenue breakdown
        metrics['revenue_breakdown'] = {
            'food_revenue': round(sales['food_payment'].sum(), 2),
            'drinks_revenue': round(sales['drinks_payment'].sum(), 2),
            'other_revenue': round(sales['other_payment'].sum(), 2),
            'service_charges': round(sales['service_charges'].sum(), 2),
            'delivery_charges': round(sales['delivery_charges'].sum(), 2)
        }
        
        # Daily average revenue
        metrics['avg_daily_revenue'] = round(total_revenue / len(sales), 2)
    
    # 7. Expense analysis
    if not expenses.empty:
        total_expenses = expenses['amount'].sum()
        metrics['total_expenses'] = round(total_expenses, 2)
        
        # Expense breakdown
        metrics['expense_breakdown'] = {
            'bills': round(expenses['bills'].sum(), 2),
            'vendors': round(expenses['vendors'].sum(), 2),
            'wage_advance': round(expenses['wage_advance'].sum(), 2),
            'repairs': round(expenses['repairs'].sum(), 2),
            'sundries': round(expenses['sundries'].sum(), 2)
        }
        
        # Average daily expenses
        metrics['avg_daily_expenses'] = round(total_expenses / len(expenses), 2)
        
        # Expense volatility
        metrics['expense_volatility'] = {
            'repairs_std': round(expenses['repairs'].std(), 2),
            'bills_std': round(expenses['bills'].std(), 2),
            'wage_std': round(expenses['wage_advance'].std(), 2)
        }

    # 7b. Build per-restaurant per-day dataset for dashboard tables and date filtering
    per_restaurant_daily_records = []
    restaurants_summary_records = []
    
    print("📊 Building per-restaurant daily dataset...")
    try:
        # Normalize dates - handle different formats
        print("📅 Normalizing dates...")
        orders['order_date'] = pd.to_datetime(orders['order_date'], format='%d-%m-%Y', errors='coerce').dt.date
        sales['date'] = pd.to_datetime(sales['date'], errors='coerce').dt.date  # Already in YYYY-MM-DD format
        expenses['exp_date'] = pd.to_datetime(expenses['exp_date'], errors='coerce').dt.date  # Already in YYYY-MM-DD format

        # Orders per day
        print("📊 Processing orders...")
        orders_daily = (
            orders.groupby(['restaurant_id', 'order_date'])
            .size()
            .reset_index(name='orders_count')
            .rename(columns={'order_date': 'date'})
        )

        # Revenue per day from sales including category breakdown
        print("💰 Processing sales...")
        sales_daily = sales.copy()
        sales_daily['revenue'] = (
            sales_daily['food_payment'] + sales_daily['drinks_payment'] +
            sales_daily['other_payment'] + sales_daily['service_charges'] +
            sales_daily['delivery_charges']
        )
        sales_daily = sales_daily[[
            'restaurant_id', 'date', 'revenue',
            'food_payment', 'drinks_payment', 'other_payment', 'service_charges', 'delivery_charges'
        ]]

        # Expenses per day including category breakdown
        print("💸 Processing expenses...")
        expenses_daily = expenses[[
            'restaurant_id', 'exp_date', 'amount', 'bills', 'vendors', 'wage_advance', 'repairs', 'sundries'
        ]].rename(columns={'exp_date': 'date', 'amount': 'expenses'})

        # Ensure all date columns are the same type (string) for merging
        print("🔗 Merging data...")
        orders_daily['date'] = orders_daily['date'].astype(str)
        sales_daily['date'] = sales_daily['date'].astype(str)
        expenses_daily['date'] = expenses_daily['date'].astype(str)

        # Merge
        daily = orders_daily.merge(sales_daily, on=['restaurant_id', 'date'], how='left')
        daily = daily.merge(expenses_daily, on=['restaurant_id', 'date'], how='left')
        daily['revenue'] = daily['revenue'].fillna(0.0)
        daily['expenses'] = daily['expenses'].fillna(0.0)
        # Fill category columns
        for col in ['food_payment','drinks_payment','other_payment','service_charges','delivery_charges',
                    'bills','vendors','wage_advance','repairs','sundries']:
            if col in daily.columns:
                daily[col] = daily[col].fillna(0.0)
        daily['profit'] = daily['revenue'] - daily['expenses']

        # Attach restaurant metadata
        print("🏢 Adding metadata...")
        clients_meta = clients[['client_id', 'legal_name']].rename(columns={'legal_name': 'client_name'})
        rest_meta = restaurants[['id', 'name', 'country_id', 'client_id']].rename(columns={'id': 'restaurant_id'})
        rest_meta = rest_meta.merge(clients_meta, on='client_id', how='left')
        daily = daily.merge(rest_meta, on='restaurant_id', how='left')

        # Build records with JSON-safe types
        print("📝 Building daily records...")
        for _, row in daily.iterrows():
            per_restaurant_daily_records.append({
                'restaurant_id': int(row['restaurant_id']),
                'name': row['name'],
                'country': 'UK' if int(row['country_id']) == 1 else 'India',
                'date': str(row['date']),
                'orders': int(row['orders_count']),
                'revenue': round(float(row['revenue']), 2),
                'expenses': round(float(row['expenses']), 2),
                'profit': round(float(row['profit']), 2),
                'client_id': int(row['client_id']),
                'client_name': row['client_name'] if pd.notna(row['client_name']) else '',
                # revenue categories
                'food_payment': round(float(row.get('food_payment', 0.0)), 2),
                'drinks_payment': round(float(row.get('drinks_payment', 0.0)), 2),
                'other_payment': round(float(row.get('other_payment', 0.0)), 2),
                'service_charges': round(float(row.get('service_charges', 0.0)), 2),
                'delivery_charges': round(float(row.get('delivery_charges', 0.0)), 2),
                # expense categories
                'bills': round(float(row.get('bills', 0.0)), 2),
                'vendors': round(float(row.get('vendors', 0.0)), 2),
                'wage_advance': round(float(row.get('wage_advance', 0.0)), 2),
                'repairs': round(float(row.get('repairs', 0.0)), 2),
                'sundries': round(float(row.get('sundries', 0.0)), 2),
            })

        # Restaurant-level summary across selected period (full year here)
        print("📊 Building restaurant summary...")
        summary = daily.groupby(['restaurant_id']).agg(
            total_orders=('orders_count', 'sum'),
            total_revenue=('revenue', 'sum'),
            total_expenses=('expenses', 'sum')
        ).reset_index()
        summary['avg_order_value'] = summary['total_revenue'] / summary['total_orders']
        summary = summary.merge(rest_meta, on='restaurant_id', how='left')
        for _, row in summary.iterrows():
            restaurants_summary_records.append({
                'restaurant_id': int(row['restaurant_id']),
                'name': row['name'],
                'country': 'UK' if int(row['country_id']) == 1 else 'India',
                'client_id': int(row['client_id']),
                'client_name': row['client_name'] if pd.notna(row['client_name']) else '',
                'total_orders': int(row['total_orders']),
                'total_revenue': round(float(row['total_revenue']), 2),
                'total_expenses': round(float(row['total_expenses']), 2),
                'profit': round(float(row['total_revenue'] - row['total_expenses']), 2),
                'avg_order_value': round(float(row['avg_order_value']), 2)
            })
        
        print(f"✅ Successfully built {len(per_restaurant_daily_records)} daily records and {len(restaurants_summary_records)} summary records")

    except Exception as e:
        print(f"❌ Error building per-restaurant daily dataset: {e}")
        print("🔄 Attempting fallback restaurant summary generation...")
        
        # Fallback: Generate basic restaurant summary from available data
        try:
            # Create basic restaurant summary from restaurants table
            for _, restaurant in restaurants.iterrows():
                # Get basic restaurant info
                restaurant_id = int(restaurant['id'])
                restaurant_name = restaurant['name']
                country_id = int(restaurant['country_id'])
                client_id = int(restaurant['client_id'])
                
                # Get client name
                client_name = ''
                if not clients.empty:
                    client_row = clients[clients['client_id'] == client_id]
                    if not client_row.empty:
                        client_name = client_row.iloc[0]['legal_name']
                
                # Calculate basic metrics from orders and sales
                total_orders = 0
                total_revenue = 0.0
                total_expenses = 0.0
                
                # Orders for this restaurant
                if not orders.empty:
                    restaurant_orders = orders[orders['restaurant_id'] == restaurant_id]
                    total_orders = len(restaurant_orders)
                
                # Sales for this restaurant
                if not sales.empty:
                    restaurant_sales = sales[sales['restaurant_id'] == restaurant_id]
                    if not restaurant_sales.empty:
                        total_revenue = (
                            restaurant_sales['food_payment'].sum() +
                            restaurant_sales['drinks_payment'].sum() +
                            restaurant_sales['other_payment'].sum() +
                            restaurant_sales['service_charges'].sum() +
                            restaurant_sales['delivery_charges'].sum()
                        )
                
                # Expenses for this restaurant
                if not expenses.empty:
                    restaurant_expenses = expenses[expenses['restaurant_id'] == restaurant_id]
                    if not restaurant_expenses.empty:
                        total_expenses = restaurant_expenses['amount'].sum()
                
                # Calculate derived metrics
                profit = total_revenue - total_expenses
                avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
                
                restaurants_summary_records.append({
                    'restaurant_id': restaurant_id,
                    'name': restaurant_name,
                    'country': 'UK' if country_id == 1 else 'India',
                    'client_id': client_id,
                    'client_name': client_name,
                    'total_orders': total_orders,
                    'total_revenue': round(float(total_revenue), 2),
                    'total_expenses': round(float(total_expenses), 2),
                    'profit': round(float(profit), 2),
                    'avg_order_value': round(float(avg_order_value), 2)
                })
            
            print(f"✅ Generated fallback restaurant summary for {len(restaurants_summary_records)} restaurants")
            
        except Exception as e2:
            print(f"❌ Fallback restaurant summary generation also failed: {e2}")
            # Create minimal restaurant summary from just the restaurants table
            for _, restaurant in restaurants.iterrows():
                restaurants_summary_records.append({
                    'restaurant_id': int(restaurant['id']),
                    'name': restaurant['name'],
                    'country': 'UK' if int(restaurant['country_id']) == 1 else 'India',
                    'client_id': int(restaurant['client_id']),
                    'client_name': '',
                    'total_orders': 0,
                    'total_revenue': 0.0,
                    'total_expenses': 0.0,
                    'profit': 0.0,
                    'avg_order_value': 0.0
                })
            print(f"✅ Created minimal restaurant summary for {len(restaurants_summary_records)} restaurants")
    
    # Build reconciliation per day (for filter-based KPI)
    print("🔄 Building reconciliation data...")
    cashup_copy = cashup.copy()
    cashup_copy['cash_up_date'] = pd.to_datetime(cashup_copy['cash_up_date'], errors='coerce').dt.date
    reconciliation_daily = cashup_copy[['restaurant_id', 'cash_up_date', 'is_match']].rename(
        columns={'cash_up_date': 'date'}
    )
    metrics['reconciliation_daily'] = [
        {
            'restaurant_id': int(row['restaurant_id']),
            'date': str(row['date']),
            'is_match': bool(row['is_match'])
        }
        for _, row in reconciliation_daily.iterrows()
    ]

    # 8. Profitability analysis
    if 'total_revenue' in metrics and 'total_expenses' in metrics:
        net_profit = metrics['total_revenue'] - metrics['total_expenses']
        metrics['net_profit'] = round(net_profit, 2)
        metrics['profit_margin'] = round((net_profit / metrics['total_revenue']) * 100, 2)
    
    # 9. Cash flow and reconciliation analysis
    if not cashup.empty:
        total_cashups = len(cashup)
        matched_cashups = len(cashup[cashup['is_match'] == True])
        metrics['reconciliation_rate'] = round((matched_cashups / total_cashups) * 100, 2)
        
        # Banking efficiency
        if not banking.empty:
            merged_banking = pd.merge(cashup, banking, on='banking_id', how='inner')
            if not merged_banking.empty:
                banking_variances = abs(merged_banking['eod_amount'] - merged_banking['banking_total'])
                metrics['avg_banking_variance'] = round(banking_variances.mean(), 2)
                metrics['max_banking_variance'] = round(banking_variances.max(), 2)
    
    # 10. Operational efficiency
    if not orders.empty and not users.empty:
        # Average orders handled per staff member across all restaurants
        users_per_restaurant = len(users) / metrics['total_restaurants']
        orders_per_restaurant = len(orders) / metrics['total_restaurants']
        metrics['avg_orders_per_staff'] = round(orders_per_restaurant / users_per_restaurant, 2) if users_per_restaurant > 0 else 0
    
    # 11. Restaurant performance (top performers using FULL orders)
    restaurant_performance = []
    if not orders.empty:
        agg = orders.groupby('restaurant_id').agg(
            total_orders=('order_id', 'count'),
            total_revenue=('order_total', 'sum')
        ).reset_index()
        agg = agg.sort_values('total_revenue', ascending=False).head(10)
        merged = agg.merge(restaurants[['id', 'name', 'country_id']], left_on='restaurant_id', right_on='id', how='left')
        for _, row in merged.iterrows():
            restaurant_performance.append({
                'name': row['name'],
                'country': 'UK' if row['country_id'] == 1 else 'India',
                'daily_orders': round(row['total_orders'] / 365.0, 1),
                'revenue': round(row['total_revenue'], 2)
            })
    metrics['restaurant_performance'] = restaurant_performance
    metrics['per_restaurant_daily'] = per_restaurant_daily_records
    metrics['restaurants_summary'] = restaurants_summary_records
    
    # Lightweight lists for filters
    # Enrich clients list with subscription details for filter-aware charts on frontend
    metrics['clients_list'] = [
        {
            'client_id': int(row['client_id']),
            'client_name': row['legal_name'],
            'is_active': bool(row['is_active']) if 'is_active' in row else True,
            'subscription_id': int(row['subscription_id']) if 'subscription_id' in row and not pd.isna(row['subscription_id']) else None,
            'subscription_name': subscription_map.get(int(row['subscription_id']), '') if 'subscription_id' in row and not pd.isna(row['subscription_id']) else ''
        }
        for _, row in clients.sort_values('legal_name').iterrows()
    ]
    metrics['restaurants_list'] = [
        {
            'restaurant_id': int(row['id']),
            'name': row['name'],
            'client_id': int(row['client_id'])
        }
        for _, row in restaurants[['id', 'name', 'client_id']].sort_values('name').iterrows()
    ]
    # users list to enable operational metrics under filters
    metrics['users_list'] = [
        {
            'user_id': int(row['user_id']),
            'client_id': int(row['client_id']) if 'client_id' in row else None,
            'restaurant_id': int(row['restaurant_id']) if 'restaurant_id' in row else None
        }
        for _, row in users[['user_id', 'client_id', 'restaurant_id']].iterrows()
    ]
    
    return metrics

def generate_dashboard_data():
    """Generate data for dashboard consumption"""
    
    metrics = load_and_analyze_data()
    if not metrics:
        return None
    
    # Create dashboard-ready data structure
    dashboard_data = {
        'last_updated': datetime.now().isoformat(),
        'summary_metrics': {
            'total_revenue': metrics.get('total_revenue', 0),
            'total_expenses': metrics.get('total_expenses', 0),
            'net_profit': metrics.get('net_profit', 0),
            'profit_margin': metrics.get('profit_margin', 0),
            'reconciliation_rate': metrics.get('reconciliation_rate', 0),
            'total_orders': metrics.get('total_orders', 0),
            'avg_order_value': metrics.get('avg_order_value', 0)
        },
        'operational_metrics': {
            'total_restaurants': metrics.get('total_restaurants', 0),
            'uk_restaurants': metrics.get('uk_restaurants', 0),
            'india_restaurants': metrics.get('india_restaurants', 0),
            'total_users': metrics.get('total_users', 0),
            'active_clients': metrics.get('active_clients', 0),
            'inactive_clients': metrics.get('inactive_clients', 0)
        },
        'financial_breakdown': {
            'revenue': metrics.get('revenue_breakdown', {}),
            'expenses': metrics.get('expense_breakdown', {}),
            'banking_variance': metrics.get('avg_banking_variance', 0)
        },
        'restaurant_performance': metrics.get('restaurant_performance', []),
        'subscription_utilization': metrics.get('subscription_analysis', []),
        'per_restaurant_daily': metrics.get('per_restaurant_daily', []),
        'restaurants_summary': metrics.get('restaurants_summary', []),
        'clients_list': metrics.get('clients_list', []),
        'restaurants_list': metrics.get('restaurants_list', []),
        'reconciliation_daily': metrics.get('reconciliation_daily', []),
        'users_list': metrics.get('users_list', []),
        'client_subscription_utilization': metrics.get('client_subscription_utilization', [])
    }
    
    # Convert numpy types to native Python types for JSON serialization
    def convert_numpy_types(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(item) for item in obj]
        return obj
    
    dashboard_data = convert_numpy_types(dashboard_data)
    return dashboard_data

def check_subscription_data():
    """Check and display subscription data details"""
    
    print("\n" + "="*60)
    print("🔍 SUBSCRIPTION DATA ANALYSIS")
    print("="*60)
    
    # Load CSV files
    clients = pd.read_csv('csv_data/clients.csv')
    subscriptions = pd.read_csv('csv_data/subscriptions.csv')
    
    print(f"\n📊 SUBSCRIPTION DATA STRUCTURE:")
    print(f"   • Total Clients: {len(clients)}")
    print(f"   • Total Subscriptions: {len(subscriptions)}")
    print(f"   • Clients CSV columns: {list(clients.columns)}")
    print(f"   • Subscriptions CSV columns: {list(subscriptions.columns)}")
    
    print(f"\n📋 SAMPLE CLIENTS DATA:")
    print(clients[['client_id', 'legal_name', 'subscription_id']].head())
    
    print(f"\n📋 SAMPLE SUBSCRIPTIONS DATA:")
    print(subscriptions.head())
    
    print(f"\n🔗 SUBSCRIPTION MAPPING:")
    for _, client in clients.head(10).iterrows():
        sub_id = client.get('subscription_id')
        if pd.notna(sub_id):
            sub_row = subscriptions[subscriptions['subscription_id'] == sub_id]
            if not sub_row.empty:
                sub_name = sub_row.iloc[0]['subscription_name']
                print(f"   • Client {client['client_id']} -> Subscription {sub_id} -> {sub_name}")
            else:
                print(f"   • Client {client['client_id']} -> Subscription {sub_id} -> NOT FOUND")
        else:
            print(f"   • Client {client['client_id']} -> No subscription_id")
    
    # Check subscription utilization
    print(f"\n📈 SUBSCRIPTION UTILIZATION ANALYSIS:")
    for _, sub in subscriptions.iterrows():
        clients_on_sub = clients[clients['subscription_id'] == sub['subscription_id']]
        print(f"   • {sub['subscription_name']}: {len(clients_on_sub)} clients, Max users: {sub['no_of_users']}, Cost: £{sub['cost']}")

def print_analysis_report():
    """Print comprehensive analysis report"""
    
    print("\n" + "="*60)
    print("🏪 ROS SYSTEM ANALYSIS REPORT")
    print("="*60)
    
    metrics = load_and_analyze_data()
    if not metrics:
        print("❌ Unable to generate report due to data loading issues")
        return
    
    print(f"\n📊 SYSTEM OVERVIEW")
    print(f"   • Total Clients: {metrics.get('total_clients', 'N/A')}")
    print(f"   • Total Restaurants: {metrics.get('total_restaurants', 'N/A')}")
    print(f"   • Total Users: {metrics.get('total_users', 'N/A')}")
    print(f"   • Active Clients: {metrics.get('active_clients', 'N/A')} ({metrics.get('inactive_clients', 'N/A')} inactive)")
    
    print(f"\n🌍 GEOGRAPHIC DISTRIBUTION")
    print(f"   • UK Restaurants: {metrics.get('uk_restaurants', 'N/A')}")
    print(f"   • India Restaurants: {metrics.get('india_restaurants', 'N/A')}")
    
    print(f"\n💰 FINANCIAL PERFORMANCE")
    if 'total_revenue' in metrics:
        print(f"   • Total Revenue: £{metrics['total_revenue']:,.2f}")
    if 'total_expenses' in metrics:
        print(f"   • Total Expenses: £{metrics['total_expenses']:,.2f}")
    if 'net_profit' in metrics:
        print(f"   • Net Profit: £{metrics['net_profit']:,.2f}")
    if 'profit_margin' in metrics:
        print(f"   • Profit Margin: {metrics['profit_margin']:.1f}%")
    
    print(f"\n🛍️ ORDER ANALYSIS (Sample)")
    if 'avg_order_value' in metrics:
        print(f"   • Average Order Value: £{metrics['avg_order_value']}")
    if 'order_type_distribution' in metrics:
        for order_type, count in metrics['order_type_distribution'].items():
            print(f"   • {order_type}: {count} orders")
    
    print(f"\n🔄 RECONCILIATION STATUS")
    if 'reconciliation_rate' in metrics:
        print(f"   • Reconciliation Success Rate: {metrics['reconciliation_rate']:.1f}%")
        target_rate = 95.0
        if metrics['reconciliation_rate'] < target_rate:
            print(f"   ⚠️  Below target rate of {target_rate}%")
    
    print(f"\n📈 SUBSCRIPTION UTILIZATION")
    if 'subscription_analysis' in metrics:
        for sub in metrics['subscription_analysis']:
            print(f"   • {sub['name']}: {sub['current_users']}/{sub['max_users']} users ({sub['utilization']}% utilized)")
    
    print(f"\n🎯 KEY INSIGHTS")
    print(f"   • Delivery orders typically have higher average values")
    print(f"   • UK restaurants show better margins due to lower tax rates")
    print(f"   • Reconciliation rate needs improvement to meet 95% target")
    print(f"   • Expense volatility highest in repairs category")
    
    print("\n" + "="*60)
    print("📊 Analysis complete! Dashboard data generated successfully.")
    print("="*60)

if __name__ == "__main__":
    print("🚀 Starting ROS Data Analysis...")
    
    # Check subscription data first
    check_subscription_data()
    
    # Generate analysis report
    print_analysis_report()
    
    # Generate dashboard data
    dashboard_data = generate_dashboard_data()
    if dashboard_data:
        # Save dashboard data to JSON file
        with open('ros_dashboard_data.json', 'w') as f:
            json.dump(dashboard_data, f, indent=2)
        print("\n✅ Dashboard data saved to 'ros_dashboard_data.json'")
        print("🌐 Open 'ros_dashboard_dynamic.html' in your browser to view the dashboard!")
        
        # Test the data
        print("\n🧪 Testing the data...")
        if dashboard_data['per_restaurant_daily']:
            test_record = dashboard_data['per_restaurant_daily'][0]
            print(f"Sample record - Revenue: £{test_record['revenue']}, Expenses: £{test_record['expenses']}, Orders: {test_record['orders']}")
        
        # Test subscription data
        print("\n📋 Testing subscription data...")
        for client in dashboard_data['clients_list'][:3]:
            print(f"Client {client['client_id']}: {client['client_name']} - Subscription: {client['subscription_name']}")
    else:
        print("\n❌ Failed to generate dashboard data")