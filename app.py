import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def load_data(file):
    df = pd.read_csv(file, parse_dates=['Payment Date'])
    return df

def filter_data(df, start_date, end_date):
    return df[(df['Payment Date'] >= start_date) & (df['Payment Date'] <= end_date)]

def get_trend_indicator(current, previous):
    if current > previous:
        return "🟢 ▲"
    elif current < previous:
        return "🔴 ▼"
    else:
        return "⚪ ▬"

def get_date_range_summary(df, days, end_date=None):
    if end_date is None:
        end_date = df['Payment Date'].max()
    start_date = end_date - timedelta(days=days)
    date_range_df = df[(df['Payment Date'] > start_date) & (df['Payment Date'] <= end_date)]
    
    total_sales = date_range_df['Order Total'].sum()
    tickets_sold = date_range_df['Ticket ID'].count()
    avg_ticket_price = total_sales / tickets_sold if tickets_sold > 0 else 0
    
    # Calculate trend
    previous_start = start_date - timedelta(days=days)
    previous_df = df[(df['Payment Date'] > previous_start) & (df['Payment Date'] <= start_date)]
    previous_sales = previous_df['Order Total'].sum()
    trend = get_trend_indicator(total_sales, previous_sales)
    
    return {
        "trend": trend,
        "sales": total_sales,
        "tickets": tickets_sold,
        "avg_price": avg_ticket_price
    }

def get_breakdown(df, period):
    if period == 'Day':
        return df.groupby(df['Payment Date'].dt.date).agg({
            'Order Total': 'sum',
            'Ticket ID': 'count'
        }).reset_index()
    elif period == 'Week':
        return df.groupby(pd.Grouper(key='Payment Date', freq='W-MON')).agg({
            'Order Total': 'sum',
            'Ticket ID': 'count'
        }).reset_index()
    elif period == 'Month':
        return df.groupby(pd.Grouper(key='Payment Date', freq='M')).agg({
            'Order Total': 'sum',
            'Ticket ID': 'count'
        }).reset_index()
    elif period == 'Year':
        return df.groupby(df['Payment Date'].dt.year).agg({
            'Order Total': 'sum',
            'Ticket ID': 'count'
        }).reset_index()

def main():
    st.title('Ticket Sales Analysis')

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file is not None:
        df = load_data(uploaded_file)

        st.subheader('Summary for Last 30, 60, and 90 Days')
        col1, col2, col3 = st.columns(3)
        
        current_date = datetime.now().date()
        for i, days in enumerate([30, 60, 90]):
            summary = get_date_range_summary(df, days, end_date=pd.Timestamp(current_date))
            with [col1, col2, col3][i]:
                st.markdown(f"""
                <div style="border:1px solid #ddd; padding:10px; border-radius:5px;">
                    <h4 style="margin-top:0;">Last {days} days</h4>
                    <p><strong style="font-size:0.9em;">Sales:</strong> {summary['trend']} ${summary['sales']:,.2f}</p>
                    <p><strong style="font-size:0.9em;">Tickets sold:</strong> {summary['tickets']:,}</p>
                    <p><strong style="font-size:0.9em;">Avg Price:</strong> ${summary['avg_price']:,.2f}</p>
                </div>
                """, unsafe_allow_html=True)

        st.subheader('30-Day Block Breakdown')
        for i in range(3):
            end_date = current_date - timedelta(days=i*30)
            summary = get_date_range_summary(df, 30, end_date=pd.Timestamp(end_date))
            st.markdown(f"""
            <div style="border:1px solid #ddd; padding:10px; border-radius:5px; margin-bottom:10px;">
                <h4 style="margin-top:0;">Days {i*30+1}-{(i+1)*30}</h4>
                <p><strong style="font-size:0.9em;">Sales:</strong> ${summary['sales']:,.2f}</p>
                <p><strong style="font-size:0.9em;">Tickets sold:</strong> {summary['tickets']:,}</p>
                <p><strong style="font-size:0.9em;">Avg Price:</strong> ${summary['avg_price']:,.2f}</p>
            </div>
            """, unsafe_allow_html=True)

        st.subheader('Detailed Breakdown')
        period = st.selectbox('Select time period', ['Day', 'Week', 'Month', 'Year', 'Custom'])
        
        if period == 'Custom':
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input('Start date', df['Payment Date'].min().date())
            with col2:
                end_date = st.date_input('End date', df['Payment Date'].max().date())
            filtered_df = filter_data(df, start_date, end_date)
            breakdown_df = get_breakdown(filtered_df, 'Day')
        else:
            breakdown_df = get_breakdown(df, period)

        breakdown_df['Avg Price'] = breakdown_df['Order Total'] / breakdown_df['Ticket ID']
        st.dataframe(breakdown_df.style.format({
            'Order Total': '${:,.2f}',
            'Avg Price': '${:,.2f}'
        }), use_container_width=True)

        st.subheader('Sales and Tickets Over Time')
        fig = go.Figure()
        fig.add_trace(go.Bar(x=breakdown_df['Payment Date'], y=breakdown_df['Order Total'], name='Total Sales', yaxis='y1'))
        fig.add_trace(go.Scatter(x=breakdown_df['Payment Date'], y=breakdown_df['Ticket ID'], name='Tickets Sold', yaxis='y2'))
        fig.update_layout(
            yaxis=dict(title='Total Sales', side='left'),
            yaxis2=dict(title='Tickets Sold', side='right', overlaying='y'),
            barmode='group'
        )
        st.plotly_chart(fig, use_container_width=True)

        ticket_type_df = df.groupby('Ticket Type').agg({'Ticket ID': 'count', 'Order Total': 'sum'}).reset_index()
        
        st.subheader('Ticket Type Breakdown')
        fig_pie = px.pie(ticket_type_df, values='Ticket ID', names='Ticket Type', title='Ticket Types Sold')
        st.plotly_chart(fig_pie, use_container_width=True)

if __name__ == '__main__':
    main()