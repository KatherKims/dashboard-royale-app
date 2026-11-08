"""Plain-language machine availability, using actual scheduled hours."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def duration(hours):
    minutes = float(hours) * 60
    if minutes == 0:
        return '0 min'
    if minutes < 1:
        return f'{minutes * 60:.0f} sec'
    total = round(minutes)
    h, m = divmod(total, 60)
    return f'{h:,} hr {m:02d} min' if h else f'{m} min'


def availability_periods(daily, monthly=True):
    rows = daily.copy()
    rows['period'] = rows.gaming_date.dt.to_period('M').dt.to_timestamp() if monthly else rows.gaming_date
    rows['affected_day'] = rows.down_hours > 1e-8
    summary = rows.groupby('period', as_index=False).agg(
        active_days=('gaming_date', 'nunique'), scheduled_hours=('scheduled_hours', 'sum'),
        available_hours=('available_hours', 'sum'), down_hours=('down_hours', 'sum'),
        affected_days=('affected_day', 'sum'), opportunity=('missed_theo_mid', 'sum'))
    summary['availability_pct'] = 100 * summary.available_hours / summary.scheduled_hours.replace(0, float('nan'))
    return summary


def render_availability(daily, machine, start_date, end_date, chart):
    st.markdown('### Could this machine be played?')
    st.caption('Availability means the machine was ready to accept play. It does not mean someone was playing it. Downtime means scheduled time when it was unavailable; it does not identify the cause.')
    available = daily.available_hours.sum()
    scheduled = daily.scheduled_hours.sum()
    down = daily.down_hours.sum()
    days = daily.gaming_date.nunique()
    affected = int((daily.down_hours > 1e-8).sum())
    rate = available / scheduled if scheduled else float('nan')
    st.write(f'**{machine} · {start_date:%b %d}–{end_date:%b %d, %Y}**: ready for **{available:,.1f} of {scheduled:,.1f} scheduled hours**. It was unavailable for **{duration(down)}** across **{affected} of {days} active days**.')
    metrics = st.columns(4)
    metrics[0].metric('Days on the floor', f'{days:,}')
    metrics[1].metric('Time ready to play', f'{rate:.2%}' if scheduled else 'No scheduled time')
    metrics[2].metric('Total time unavailable', duration(down))
    metrics[3].metric('Days with some downtime', f'{affected} of {days}')
    st.caption('Only active records inside your date selection are counted. Time before installation or after retirement is excluded. Scheduled hours respect the 23-hour daylight-saving gaming day; percentages use total hours, not an average of daily percentages.')

    view = st.radio('Show unavailable time by', ['Month', 'Day'], horizontal=True, key='availability_detail')
    monthly = view == 'Month'
    periods = availability_periods(daily, monthly)
    units = 'hours' if periods.down_hours.max() >= 2 else 'minutes'
    amount = periods.down_hours if units == 'hours' else periods.down_hours * 60
    labels = periods.period.dt.strftime('%b %Y' if monthly else '%b %d, %Y')
    detail = pd.DataFrame({'label': labels, 'available': periods.available_hours,
                           'scheduled': periods.scheduled_hours, 'pct': periods.availability_pct,
                           'days': periods.affected_days})
    fig = go.Figure(go.Bar(
        x=labels, y=amount, marker_color='#FF756B', name=f'Unavailable {units}',
        text=[f'{x:,.1f}' if x else '' for x in amount] if monthly else None,
        textposition='outside', cliponaxis=False, customdata=detail.to_numpy(),
        hovertemplate='<b>%{customdata[0]}</b><br>Unavailable: %{y:,.2f} ' + units +
                      '<br>Ready: %{customdata[1]:,.2f} / %{customdata[2]:,.2f} hours' +
                      '<br>Availability: %{customdata[3]:.2f}%<br>Days with downtime: %{customdata[4]}<extra></extra>'))
    fig.update_yaxes(title=f'Time unavailable ({units})', rangemode='tozero')
    fig.update_xaxes(title=None, type='category', nticks=8 if not monthly else 6)
    chart(fig, 'When was this machine unavailable?', 'machine_availability', height=360)
    st.caption('Taller bars mean more unavailable time. A zero bar means no recorded downtime on an active day. Monthly bars include only the selected dates, so the first or last month may be partial. Gaming days run from 6 a.m. to 6 a.m. Las Vegas time.')

    if affected:
        worst = daily.loc[daily.down_hours.idxmax()]
        st.info(f'Largest daily interruption total: {worst.gaming_date:%B %d, %Y} — {duration(worst.down_hours)} unavailable. This is the combined downtime recorded for that gaming day, not necessarily one outage.')
    else:
        st.info('No downtime was recorded for this machine in the selected active days.')
    opportunity = daily.missed_theo_mid.sum()
    st.write(f'**What could that time have earned?** Estimated expected-earnings opportunity: **${opportunity:,.2f}**, before costs. This uses historical play rates. It is not a measured cash loss: guests may have played another machine instead.')

    with st.expander('Read the numbers or download them'):
        table = pd.DataFrame({
            'Month' if monthly else 'Gaming date': labels,
            'Days on floor': periods.active_days,
            'Scheduled hours': periods.scheduled_hours.round(2),
            'Ready hours': periods.available_hours.round(2),
            'Unavailable hours': periods.down_hours.round(3),
            'Ready (%)': periods.availability_pct.round(2),
            'Days with downtime': periods.affected_days,
            'Estimated earnings opportunity ($)': periods.opportunity.round(2)})
        st.dataframe(table, hide_index=True, width='stretch')
        st.download_button('Download availability details', table.to_csv(index=False).encode(),
                           f'{machine}_availability_{start_date:%Y%m%d}_{end_date:%Y%m%d}.csv',
                           'text/csv', key='download_availability_details')
