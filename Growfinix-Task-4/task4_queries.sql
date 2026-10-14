
-- 1. Display all media production records
SELECT *
FROM media_costs;

-- 2. Calculate total production cost by media format
SELECT
    Media_Format,
    SUM(Production_Cost) AS Total_Cost
FROM media_costs
GROUP BY Media_Format;

-- 3. Calculate revenue by media format
SELECT
    Media_Format,
    SUM(Revenue) AS Total_Revenue
FROM media_costs
GROUP BY Media_Format;

-- 4. Calculate profit by media format
SELECT
    Media_Format,
    SUM(Revenue) - SUM(Production_Cost) AS Total_Profit
FROM media_costs
GROUP BY Media_Format;

-- 5. Calculate ROI percentage by media format
SELECT
    Media_Format,
    SUM(Production_Cost) AS Total_Cost,
    SUM(Revenue) AS Total_Revenue,
    SUM(Revenue) - SUM(Production_Cost) AS Total_Profit,
    ROUND(
        100.0 * (SUM(Revenue) - SUM(Production_Cost))
        / NULLIF(SUM(Production_Cost), 0),
        2
    ) AS ROI_Percentage
FROM media_costs
GROUP BY Media_Format;
