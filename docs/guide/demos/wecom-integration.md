# WeCom Integration

Calculate department efficiency and send reports to WeCom.

## Demo

![Department Efficiency Statistics & Send to WeCom](/04-department-efficiency-wecom.gif)

## Prompt

```
Calculate department efficiency and send the data to WeCom. 
Efficiency formula: Efficiency = Task bid / Timelog hours
```

## What This Does

1. Retrieves task bid (estimated hours) from ShotGrid
2. Retrieves actual timelog hours
3. Calculates efficiency ratio for each department
4. Formats the report
5. Sends the report to WeCom (WeChat Work)

## Efficiency Formula

```
Efficiency = Task Bid Hours / Actual Timelog Hours
```

- **> 100%**: Under budget (efficient)
- **= 100%**: On budget
- **< 100%**: Over budget (needs attention)

## Use Cases

- Daily/weekly efficiency reports
- Department performance tracking
- Automated notifications to management
- KPI monitoring and alerts
