import sqlite3
from datetime import datetime, timedelta, date

conn = sqlite3.connect('cypher_label_guard.db')
cur = conn.cursor()

def get_analytics(period="Today"):
    cur.execute("SELECT MAX(date(created_at)) FROM job_records")
    latest_str = cur.fetchone()[0] or datetime.now().strftime("%Y-%m-%d")
    ref_date = datetime.strptime(latest_str, "%Y-%m-%d").date()
    
    if period == "Today":
        start_date = ref_date
        prev_date = ref_date - timedelta(days=1)
        
        # Total metrics for today
        cur.execute("""
            SELECT count(*), coalesce(sum(labels_count), 0),
                   sum(CASE WHEN consensus_label NOT LIKE '%REJECT%' THEN 1 ELSE 0 END),
                   coalesce(sum(CAST(REPLACE(cost, '$', '') as FLOAT)), 0)
            FROM job_records
            WHERE date(created_at) = ?
        """, (start_date.isoformat(),))
        total_jobs, total_labels, completed_ok, total_cost = cur.fetchone()
        
        # Previous period (yesterday)
        cur.execute("""
            SELECT coalesce(sum(labels_count), 0)
            FROM job_records
            WHERE date(created_at) = ?
        """, (prev_date.isoformat(),))
        prev_labels = cur.fetchone()[0]
        
        # Hourly time series today vs yesterday
        cur.execute("""
            SELECT strftime('%H:00', created_at) as hr, coalesce(sum(labels_count), 0)
            FROM job_records
            WHERE date(created_at) = ?
            GROUP BY hr
        """, (start_date.isoformat(),))
        today_hr = dict(cur.fetchall())
        
        cur.execute("""
            SELECT strftime('%H:00', created_at) as hr, coalesce(sum(labels_count), 0)
            FROM job_records
            WHERE date(created_at) = ?
            GROUP BY hr
        """, (prev_date.isoformat(),))
        prev_hr = dict(cur.fetchall())
        
        time_series = []
        for h in range(24):
            hr_str = f"{h:02d}:00"
            time_series.append({
                "time": hr_str,
                "labels": today_hr.get(hr_str, 0),
                "previous": prev_hr.get(hr_str, 0),
            })
            
    elif period == "Last 7 days":
        start_date = ref_date - timedelta(days=6)
        prev_start = ref_date - timedelta(days=13)
        prev_end = ref_date - timedelta(days=7)
        
        cur.execute("""
            SELECT count(*), coalesce(sum(labels_count), 0),
                   sum(CASE WHEN consensus_label NOT LIKE '%REJECT%' THEN 1 ELSE 0 END),
                   coalesce(sum(CAST(REPLACE(cost, '$', '') as FLOAT)), 0)
            FROM job_records
            WHERE date(created_at) >= ? AND date(created_at) <= ?
        """, (start_date.isoformat(), ref_date.isoformat()))
        total_jobs, total_labels, completed_ok, total_cost = cur.fetchone()
        
        cur.execute("""
            SELECT coalesce(sum(labels_count), 0)
            FROM job_records
            WHERE date(created_at) >= ? AND date(created_at) <= ?
        """, (prev_start.isoformat(), prev_end.isoformat()))
        prev_labels = cur.fetchone()[0]
        
        # Daily time series for last 7 days
        cur.execute("""
            SELECT date(created_at) as d, coalesce(sum(labels_count), 0)
            FROM job_records
            WHERE date(created_at) >= ? AND date(created_at) <= ?
            GROUP BY d
        """, (start_date.isoformat(), ref_date.isoformat()))
        curr_daily = dict(cur.fetchall())
        
        cur.execute("""
            SELECT date(created_at) as d, coalesce(sum(labels_count), 0)
            FROM job_records
            WHERE date(created_at) >= ? AND date(created_at) <= ?
            GROUP BY d
        """, (prev_start.isoformat(), prev_end.isoformat()))
        prev_daily = dict(cur.fetchall())
        
        time_series = []
        for d in range(7):
            cur_d = start_date + timedelta(days=d)
            p_d = prev_start + timedelta(days=d)
            time_series.append({
                "time": cur_d.strftime("%b %d"),
                "labels": curr_daily.get(cur_d.isoformat(), 0),
                "previous": prev_daily.get(p_d.isoformat(), 0),
            })
            
    else: # Last 30 days
        start_date = ref_date - timedelta(days=29)
        prev_start = ref_date - timedelta(days=59)
        prev_end = ref_date - timedelta(days=30)
        
        cur.execute("""
            SELECT count(*), coalesce(sum(labels_count), 0),
                   sum(CASE WHEN consensus_label NOT LIKE '%REJECT%' THEN 1 ELSE 0 END),
                   coalesce(sum(CAST(REPLACE(cost, '$', '') as FLOAT)), 0)
            FROM job_records
            WHERE date(created_at) >= ? AND date(created_at) <= ?
        """, (start_date.isoformat(), ref_date.isoformat()))
        total_jobs, total_labels, completed_ok, total_cost = cur.fetchone()
        
        cur.execute("""
            SELECT coalesce(sum(labels_count), 0)
            FROM job_records
            WHERE date(created_at) >= ? AND date(created_at) <= ?
        """, (prev_start.isoformat(), prev_end.isoformat()))
        prev_labels = cur.fetchone()[0]
        
        cur.execute("""
            SELECT date(created_at) as d, coalesce(sum(labels_count), 0)
            FROM job_records
            WHERE date(created_at) >= ? AND date(created_at) <= ?
            GROUP BY d
        """, (start_date.isoformat(), ref_date.isoformat()))
        curr_daily = dict(cur.fetchall())
        
        time_series = []
        for d in range(30):
            cur_d = start_date + timedelta(days=d)
            time_series.append({
                "time": cur_d.strftime("%b %d"),
                "labels": curr_daily.get(cur_d.isoformat(), 0),
                "previous": 0,
            })
            
    acc_pct = round((completed_ok / total_jobs * 100), 1) if total_jobs > 0 else 100.0
    
    return {
        "period": period,
        "ref_date": str(ref_date),
        "total_jobs": total_jobs,
        "total_labels": total_labels,
        "prev_labels": prev_labels,
        "accuracy_pct": acc_pct,
        "total_cost": round(total_cost, 2),
        "time_series_points": len(time_series),
        "sample_series": time_series[:3],
    }

print("Today:", get_analytics("Today"))
print("7 Days:", get_analytics("Last 7 days"))
print("30 Days:", get_analytics("Last 30 days"))
