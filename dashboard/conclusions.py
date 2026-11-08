"""A closing demo view derived from the current evidence and decision engine."""
import pandas as pd
import streamlit as st
from dashboard.decisions import rank_portfolios


def evidence_conclusions(report, summary):
    monthly = pd.DataFrame(report['monthly']).sort_values('month')
    peak = monthly.loc[monthly.wagers_per_available_hour.idxmax()]
    latest = monthly.iloc[-1]
    change = 100 * (latest.wagers_per_available_hour / peak.wagers_per_available_hour - 1)
    guests, down = report['players'], report['downtime']
    loyalty = pd.DataFrame(report['loyalty']).sort_values('gaming_month').reset_index(drop=True)
    drop = loyalty.points_per_face_dollar.diff().idxmin()
    before, after = loyalty.iloc[max(0, drop - 1)], loyalty.iloc[drop]
    flagged = summary.sort_values('standardized_gap').iloc[0]
    return [
        ('1 · Investigate before replacing',
         f'Raw earnings mix exposure, availability and payout variation. '
         f'{flagged.name} has a {flagged.standardized_gap:.2f} payout screening score but only '
         f'{flagged.downtime_hours:.1f} unavailable hours. Review its settings and meters; this is not proof of a defective machine.'),
        ('2 · Demand softened; the cause is not proven',
         f'Wagers per available machine-hour fell {abs(change):.1f}% from '
         f'{pd.Timestamp(peak.month):%B} (${peak.wagers_per_available_hour:,.2f}) to '
         f'{pd.Timestamp(latest.month):%B} (${latest.wagers_per_available_hour:,.2f}). '
         'Events, location and game mix are competing explanations, not established causes.'),
        ('3 · Downtime is an opportunity to investigate',
         f'{down["hours"]:,.0f} unavailable hours imply about ${down["missed_wagers_mid"]:,.0f} '
         f'in missed-wager opportunity and ${down["missed_theo_mid"]:,.0f} in expected earnings before costs. '
         'These are estimates, not observed floor losses; guests may switch machines. The machine view shows when downtime occurred.'),
        ('4 · Tracked play is concentrated',
         f'Tracked guests wagered ${guests["tracked_wagers"]/1e6:.2f}M, received '
         f'${guests["tracked_payouts"]/1e6:.2f}M, and had net results of '
         f'−${abs(guests["player_net"])/1e6:.2f}M. The top 1% by wagers supplied '
         f'{guests["top1pct_wager_share"]:.1%} of tracked wagers. Carded play covers '
         f'{guests["tracked_wager_coverage"]:.1%} of all wagers; do not generalize to every guest.'),
        ('5 · Comp redemption economics changed',
         f'Economic comp cost totaled ${monthly.comps.sum():,.0f}. Points redeemed per dollar of face value '
         f'fell from {before.points_per_face_dollar:.2f} in {pd.Timestamp(before.gaming_month):%B} '
         f'to {after.points_per_face_dollar:.2f} in {pd.Timestamp(after.gaming_month):%B}. '
         'Check policy and redemption mix before claiming a policy effect; evaluate changes with a controlled pilot.'),
    ]


def render_conclusions(report, engine, candidates, metadata):
    st.subheader('Final conclusions · what should the casino do?')
    st.caption('Closing view for the demo: full January–June 2025 evidence; July 1–30 decision horizon. The recommendation uses the agreed $100,000 budget, maximum expected net benefit and default assumptions (benefit multiplier 1.0). Exploratory filters and sliders do not change this baseline conclusion.')
    st.info('Low earnings are a reason to investigate—not an automatic reason to replace a machine.')
    items = evidence_conclusions(report, engine.summary)
    for title, message in items:
        st.markdown('#### ' + title)
        st.write(message)

    st.markdown('#### 6 · The $100,000 decision')
    plans = rank_portfolios(candidates, budget=100000, multiplier=1.).sort_values(
        ['Expected net benefit', 'Cost'], ascending=[False, True])
    best = plans.iloc[0]
    chosen = [c for c in candidates if c['id'] in best.Actions.split(' + ')]
    if best.Actions == 'Keep budget':
        st.success('Recommendation: retain the $100,000 for now. None of the shortlisted spending plans beats keeping the budget on expected 30-day net benefit under the default assumptions.')
    else:
        labels = '; '.join(f'{c["name"]} — {c["target"]}' for c in chosen)
        st.success('Highest modeled expected 30-day net benefit in the shortlist: ' + labels + '. Validate assumptions and operating feasibility before funding.')
    a, b, c = st.columns(3)
    a.metric('Recommended spending', f'${best.Cost:,.0f}')
    b.metric('Budget retained', f'${100000 - best.Cost:,.0f}')
    net = best['Expected net benefit']
    c.metric('Modeled incremental net benefit', f'−${abs(net):,.0f}' if net < 0 else f'${net:,.0f}')
    st.caption(f'{len(candidates)} candidates · {len(plans)} feasible portfolios · 1,000 assumption-based scenarios. Retained budget is unspent cash, not profit. This is a limited comparison, not proof that every possible investment is unattractive. Inspection and pilots can have learning value that is not priced here.')

    improvement = 1 - metadata['holdout_mae'] / metadata['baseline_mae']
    st.markdown('#### Why use the forecast?')
    st.write(f'The weekday model reduced May–June machine-day prediction error by **{improvement:.1%}** '
             f'(${metadata["baseline_mae"]:,.0f} → ${metadata["holdout_mae"]:,.0f} MAE) against a constant baseline. '
             'Its July demand forecast informs move, lease and signage calculations. It predicts wagers, not payout luck or the causal benefit of an action. Error bands are approximate.')
    st.markdown('#### How we would know an action worked')
    st.write('1. Record the target, action date, costs and comparison group before starting.\n'
             '2. Compare availability and expected earnings per scheduled hour against similar untreated machines; check total floor play for displacement.\n'
             '3. Require positive incremental contribution after costs, with uncertainty reported. If 30 days are inconclusive, collect more evidence rather than claim success.')
    st.markdown('**Closing takeaway: Diagnose the cause, test the intervention, and spend only when the evidence supports it.**')
    with st.expander('Trace these conclusions to evidence'):
        st.write('Questions 1–3: machine/property daily exports, payout variance and downtime estimates. Questions 4–5: grouped player outcomes and reconciled loyalty ledger. Question 6: action catalogue and the current shared DecisionEngine. Model validation: forecast_metadata.json and the frozen demand_predictions export. The sidebar Claims & Evidence appendix documents transformations, alternatives and limitations.')
        table = pd.DataFrame([{'Action': x['name'], 'Target': x['target'], 'Cash cost ($)': x['cost'],
                               'Expected net benefit ($)': x['expected_net'], '10th percentile ($)': x['p10'],
                               '90th percentile ($)': x['p90']} for x in candidates])
        st.dataframe(table, hide_index=True, width='stretch')
