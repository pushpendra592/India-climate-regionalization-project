const {
  Presentation,
  PresentationFile,
  row,
  column,
  grid,
  text,
  chart,
  rule,
  fill,
  hug,
  fixed,
  wrap,
  fr,
  auto,
} = await import("@oai/artifact-tool");

const WIDTH = 1920;
const HEIGHT = 1080;
const BG = "#FFFDF9";
const INK = "#16213E";
const SUBTLE = "#5B6475";
const ACCENT = "#D62828";
const ACCENT_SOFT = "#FDECEC";
const BLUE = "#1F6E8C";

const deck = Presentation.create({
  slideSize: { width: WIDTH, height: HEIGHT },
});

function bulletBlock(lines, fontSize = 24, color = INK) {
  return lines.map((line) => `• ${line}`).join("\n");
}

function addHeader(slide, section, title, subtitle = "") {
  slide.compose(
    column(
      {
        name: "root",
        width: fill,
        height: fill,
        padding: { x: 88, y: 72 },
        gap: 20,
      },
      [
        text(section.toUpperCase(), {
          name: "section",
          width: fill,
          height: hug,
          style: { fontSize: 18, bold: true, color: ACCENT },
        }),
        text(title, {
          name: "title",
          width: wrap(1450),
          height: hug,
          style: { fontSize: 50, bold: true, color: INK },
        }),
        rule({ name: "accent-rule", width: fixed(220), stroke: ACCENT, weight: 4 }),
        subtitle
          ? text(subtitle, {
              name: "subtitle",
              width: wrap(1500),
              height: hug,
              style: { fontSize: 24, color: SUBTLE },
            })
          : text("", { name: "subtitle-spacer", width: fixed(1), height: fixed(1), style: { fontSize: 1 } }),
      ],
    ),
    { frame: { left: 0, top: 0, width: WIDTH, height: HEIGHT }, baseUnit: 8 },
  );
}

function addCoverSlide() {
  const slide = deck.slides.add();
  slide.compose(
    column(
      {
        name: "root",
        width: fill,
        height: fill,
        padding: { x: 96, y: 84 },
        gap: 26,
      },
      [
        text("Climate Regionalization of India", {
          name: "eyebrow",
          width: fill,
          height: hug,
          style: { fontSize: 22, bold: true, color: ACCENT },
        }),
        text("Using NASA POWER and Unsupervised Machine Learning", {
          name: "cover-title",
          width: wrap(1300),
          height: hug,
          style: { fontSize: 68, bold: true, color: INK },
        }),
        text(
          "A data-driven framework to identify climate regions across India, explain their climatic behavior, and predict the regional class of any queried place.",
          {
            name: "cover-subtitle",
            width: wrap(1260),
            height: hug,
            style: { fontSize: 30, color: SUBTLE },
          },
        ),
        grid(
          {
            name: "metrics-grid",
            width: fill,
            height: hug,
            columns: [fr(1), fr(1), fr(1)],
            columnGap: 26,
            rowGap: 0,
          },
          [
            column({ name: "metric-1", width: fill, height: hug, gap: 8 }, [
              text("1153", {
                name: "points-number",
                width: fill,
                height: hug,
                style: { fontSize: 52, bold: true, color: BLUE },
              }),
              text("Land-valid climate sample points", {
                name: "points-label",
                width: wrap(420),
                height: hug,
                style: { fontSize: 22, color: SUBTLE },
              }),
            ]),
            column({ name: "metric-2", width: fill, height: hug, gap: 8 }, [
              text("2000–2024", {
                name: "period-number",
                width: fill,
                height: hug,
                style: { fontSize: 52, bold: true, color: BLUE },
              }),
              text("Daily NASA POWER observation window", {
                name: "period-label",
                width: wrap(420),
                height: hug,
                style: { fontSize: 22, color: SUBTLE },
              }),
            ]),
            column({ name: "metric-3", width: fill, height: hug, gap: 8 }, [
              text("8", {
                name: "regions-number",
                width: fill,
                height: hug,
                style: { fontSize: 52, bold: true, color: BLUE },
              }),
              text("Final climate regions in the selected production model", {
                name: "regions-label",
                width: wrap(420),
                height: hug,
                style: { fontSize: 22, color: SUBTLE },
              }),
            ]),
          ],
        ),
        text("Prepared for project presentation | May 2026", {
          name: "cover-footer",
          width: fill,
          height: hug,
          style: { fontSize: 18, color: SUBTLE },
        }),
      ],
    ),
    { frame: { left: 0, top: 0, width: WIDTH, height: HEIGHT }, baseUnit: 8 },
  );
}

function addProblemSlide() {
  const slide = deck.slides.add();
  slide.compose(
    grid(
      {
        name: "problem-root",
        width: fill,
        height: fill,
        padding: { x: 88, y: 72 },
        columns: [fr(1.05), fr(0.95)],
        rows: [auto, fr(1)],
        columnGap: 40,
        rowGap: 30,
      },
      [
        column(
          { name: "problem-header", width: fill, height: hug, gap: 20, columnSpan: 2 },
          [
            text("Problem and Motivation", {
              name: "section",
              width: fill,
              height: hug,
              style: { fontSize: 18, bold: true, color: ACCENT },
            }),
            text("Why this project was needed", {
              name: "title",
              width: wrap(1100),
              height: hug,
              style: { fontSize: 50, bold: true, color: INK },
            }),
            rule({ name: "rule", width: fixed(220), stroke: ACCENT, weight: 4 }),
          ],
        ),
        text(
          bulletBlock([
            "India contains highly diverse climates: arid west, humid northeast, cold high mountains, monsoon plains, inland plateau, and coastal south.",
            "Traditional climate classifications are useful, but they are rule-based and do not automatically adapt to the full multidimensional structure of the observed data.",
            "A national-scale, data-driven regionalization can reveal how climatic similarity is distributed continuously across India.",
            "The project was also designed to connect climate regions with agriculture, energy, disaster risk, and urban planning use cases.",
          ]),
          {
            name: "left-bullets",
            width: fill,
            height: hug,
            style: { fontSize: 24, color: INK, breakLine: true },
          },
        ),
        column({ name: "right-highlights", width: fill, height: hug, gap: 24 }, [
          text("Core Aim", {
            name: "aim-label",
            width: fill,
            height: hug,
            style: { fontSize: 24, bold: true, color: BLUE },
          }),
          text(
            "Discover meaningful climate regions directly from long-term weather observations instead of predefining them manually.",
            {
              name: "aim-text",
              width: wrap(560),
              height: hug,
              style: { fontSize: 28, color: INK },
            },
          ),
          text("Practical Value", {
            name: "value-label",
            width: fill,
            height: hug,
            style: { fontSize: 24, bold: true, color: BLUE },
          }),
          text(
            "Support evidence-based planning for crops, renewable energy, hazard exposure, and regional environmental interpretation.",
            {
              name: "value-text",
              width: wrap(560),
              height: hug,
              style: { fontSize: 28, color: INK },
            },
          ),
        ]),
      ],
    ),
    { frame: { left: 0, top: 0, width: WIDTH, height: HEIGHT }, baseUnit: 8 },
  );
}

function addDataCollectionSlide() {
  const slide = deck.slides.add();
  slide.compose(
    grid(
      {
        name: "data-root",
        width: fill,
        height: fill,
        padding: { x: 88, y: 72 },
        columns: [fr(1), fr(1)],
        rows: [auto, fr(1)],
        columnGap: 44,
        rowGap: 30,
      },
      [
        column({ name: "head", width: fill, height: hug, gap: 18, columnSpan: 2 }, [
          text("Data Collection and Study Area", {
            name: "section",
            width: fill,
            height: hug,
            style: { fontSize: 18, bold: true, color: ACCENT },
          }),
          text("How the India-wide climate dataset was built", {
            name: "title",
            width: wrap(1200),
            height: hug,
            style: { fontSize: 50, bold: true, color: INK },
          }),
          rule({ name: "rule", width: fixed(220), stroke: ACCENT, weight: 4 }),
        ]),
        column({ name: "left", width: fill, height: hug, gap: 18 }, [
          text("Study-area setup", {
            name: "setup-head",
            width: fill,
            height: hug,
            style: { fontSize: 26, bold: true, color: BLUE },
          }),
          text(
            bulletBlock([
              "Bounding grid over India: latitude 8.0° to 37.0° and longitude 68.0° to 97.5°.",
              "Grid spacing of 0.5° produced 3540 raw sample points.",
              "Land masking removed ocean and invalid border spillover points.",
              "The final land-valid analysis set contained 1153 climate sample locations.",
            ]),
            {
              name: "setup-bullets",
              width: fill,
              height: hug,
              style: { fontSize: 24, color: INK, breakLine: true },
            },
          ),
          text("NASA POWER variables collected", {
            name: "vars-head",
            width: fill,
            height: hug,
            style: { fontSize: 26, bold: true, color: BLUE },
          }),
          text(
            "Solar irradiance, clearness index, longwave radiation, UV index, temperature, dew point, earth skin temperature, relative humidity, specific humidity, precipitation, wind speed, wind direction, surface pressure, and cloud amount.",
            {
              name: "vars-text",
              width: wrap(760),
              height: hug,
              style: { fontSize: 22, color: INK },
            },
          ),
        ]),
        column({ name: "right", width: fill, height: hug, gap: 22 }, [
          text("Collection outcome", {
            name: "outcome-head",
            width: fill,
            height: hug,
            style: { fontSize: 26, bold: true, color: BLUE },
          }),
          text(
            bulletBlock([
              "Daily NASA POWER weather data collected from 2000-01-01 to 2024-12-31.",
              "Point-level files combined into one national interim dataset.",
              "Basic validation checked missingness, date continuity, physical ranges, and expected point coverage.",
              "This validated daily dataset became the single input source for all downstream preprocessing and clustering stages.",
            ]),
            {
              name: "outcome-bullets",
              width: fill,
              height: hug,
              style: { fontSize: 24, color: INK, breakLine: true },
            },
          ),
          text("Collection pipeline", {
            name: "pipeline-head",
            width: fill,
            height: hug,
            style: { fontSize: 26, bold: true, color: BLUE },
          }),
          text(
            "Grid generation → land masking → NASA POWER fetch → combine point files → validation",
            {
              name: "pipeline-text",
              width: wrap(720),
              height: hug,
              style: { fontSize: 24, color: INK },
            },
          ),
        ]),
      ],
    ),
    { frame: { left: 0, top: 0, width: WIDTH, height: HEIGHT }, baseUnit: 8 },
  );
}

function addPreprocessingSlide() {
  const slide = deck.slides.add();
  slide.compose(
    grid(
      {
        name: "prep-root",
        width: fill,
        height: fill,
        padding: { x: 88, y: 72 },
        columns: [fr(1), fr(1)],
        rows: [auto, fr(1)],
        columnGap: 44,
        rowGap: 28,
      },
      [
        column({ name: "head", width: fill, height: hug, gap: 18, columnSpan: 2 }, [
          text("Data Normalization and Cleaning", {
            name: "section",
            width: fill,
            height: hug,
            style: { fontSize: 18, bold: true, color: ACCENT },
          }),
          text("Turning raw NASA POWER values into a reliable climate table", {
            name: "title",
            width: wrap(1320),
            height: hug,
            style: { fontSize: 50, bold: true, color: INK },
          }),
          rule({ name: "rule", width: fixed(220), stroke: ACCENT, weight: 4 }),
        ]),
        column({ name: "left", width: fill, height: hug, gap: 16 }, [
          text("Normalization", {
            name: "norm-head",
            width: fill,
            height: hug,
            style: { fontSize: 26, bold: true, color: BLUE },
          }),
          text(
            bulletBlock([
              "Raw NASA parameter names were converted into project-specific clean names.",
              "Generic aliases such as temperature_2m_mean, precipitation_sum, cloud_cover_mean, and wind_speed_10m_mean were created for downstream compatibility.",
              "Daily NASA fields were aligned with the broader project schema so later steps could reuse a common climate-processing design.",
            ]),
            {
              name: "norm-bullets",
              width: fill,
              height: hug,
              style: { fontSize: 24, color: INK, breakLine: true },
            },
          ),
          text("Cleaning", {
            name: "clean-head",
            width: fill,
            height: hug,
            style: { fontSize: 26, bold: true, color: BLUE },
          }),
          text(
            bulletBlock([
              "Duplicate rows removed using latitude, longitude, and date.",
              "High-null columns dropped if missingness exceeded the configured threshold.",
              "Remaining gaps filled using interpolation, monthly location medians, and then global medians.",
            ]),
            {
              name: "clean-bullets",
              width: fill,
              height: hug,
              style: { fontSize: 24, color: INK, breakLine: true },
            },
          ),
        ]),
        column({ name: "right", width: fill, height: hug, gap: 16 }, [
          text("Reliability controls", {
            name: "reliability-head",
            width: fill,
            height: hug,
            style: { fontSize: 26, bold: true, color: BLUE },
          }),
          text(
            bulletBlock([
              "Outliers capped using the IQR method with a factor of 3.0.",
              "Physical range limits enforced for temperature, humidity, rainfall, pressure, cloud cover, wind, and solar-related fields.",
              "The aim was not to remove climate variability, but to remove invalid or unrealistic values before feature generation.",
            ]),
            {
              name: "reliability-bullets",
              width: fill,
              height: hug,
              style: { fontSize: 24, color: INK, breakLine: true },
            },
          ),
          text("Outcome", {
            name: "outcome-head",
            width: fill,
            height: hug,
            style: { fontSize: 26, bold: true, color: BLUE },
          }),
          text(
            "A cleaned daily national weather table ready for feature engineering, temporal aggregation, and climate-scale analysis.",
            {
              name: "outcome-text",
              width: wrap(720),
              height: hug,
              style: { fontSize: 26, color: INK },
            },
          ),
        ]),
      ],
    ),
    { frame: { left: 0, top: 0, width: WIDTH, height: HEIGHT }, baseUnit: 8 },
  );
}

function addFeatureEngineeringSlide() {
  const slide = deck.slides.add();
  slide.compose(
    grid(
      {
        name: "feature-root",
        width: fill,
        height: fill,
        padding: { x: 88, y: 72 },
        columns: [fr(1), fr(1)],
        rows: [auto, fr(1)],
        columnGap: 40,
        rowGap: 28,
      },
      [
        column({ name: "head", width: fill, height: hug, gap: 18, columnSpan: 2 }, [
          text("Feature Engineering", {
            name: "section",
            width: fill,
            height: hug,
            style: { fontSize: 18, bold: true, color: ACCENT },
          }),
          text("Converting weather variables into climate indicators", {
            name: "title",
            width: wrap(1200),
            height: hug,
            style: { fontSize: 50, bold: true, color: INK },
          }),
          rule({ name: "rule", width: fixed(220), stroke: ACCENT, weight: 4 }),
        ]),
        text(
          bulletBlock([
            "Core derived features: daily temperature range, humidity range, cloud stratification, sunshine fraction, and precipitation intensity.",
            "Wind extrapolation: wind speeds were projected from 10 m to 80 m, 120 m, and 180 m, followed by wind shear estimation.",
            "Energy features: wind power density at multiple hub heights, solar utilization ratio, and solar-wind complementarity.",
          ]),
          {
            name: "left-bullets",
            width: fill,
            height: hug,
            style: { fontSize: 24, color: INK, breakLine: true },
          },
        ),
        text(
          bulletBlock([
            "Agriculture features: growing degree days, frost risk, heat stress, soil temperature proxy, and soil-air temperature difference.",
            "Disaster features: heavy rain flag, extreme rain flag, flood-risk indicator, and optional wind/pressure hazard indicators.",
            "Urban features: thermal stress index, outdoor comfort score, and heat-island potential.",
          ]),
          {
            name: "right-bullets",
            width: fill,
            height: hug,
            style: { fontSize: 24, color: INK, breakLine: true },
          },
        ),
      ],
    ),
    { frame: { left: 0, top: 0, width: WIDTH, height: HEIGHT }, baseUnit: 8 },
  );
}

function addAggregationSlide() {
  const slide = deck.slides.add();
  slide.compose(
    grid(
      {
        name: "agg-root",
        width: fill,
        height: fill,
        padding: { x: 88, y: 72 },
        columns: [fr(1), fr(1)],
        rows: [auto, fr(1)],
        columnGap: 42,
        rowGap: 28,
      },
      [
        column({ name: "head", width: fill, height: hug, gap: 18, columnSpan: 2 }, [
          text("Temporal Aggregation and Climate Normals", {
            name: "section",
            width: fill,
            height: hug,
            style: { fontSize: 18, bold: true, color: ACCENT },
          }),
          text("How daily weather becomes a long-term climate signature", {
            name: "title",
            width: wrap(1300),
            height: hug,
            style: { fontSize: 50, bold: true, color: INK },
          }),
          rule({ name: "rule", width: fixed(220), stroke: ACCENT, weight: 4 }),
        ]),
        column({ name: "left", width: fill, height: hug, gap: 16 }, [
          text("Aggregation levels", {
            name: "levels-head",
            width: fill,
            height: hug,
            style: { fontSize: 26, bold: true, color: BLUE },
          }),
          text(
            bulletBlock([
              "Monthly aggregation grouped data by latitude, longitude, year, and month.",
              "Seasonal aggregation used Winter, Pre-Monsoon, Monsoon, and Post-Monsoon.",
              "Yearly aggregation summarized each location’s annual climatic behavior.",
              "Climate normals averaged long-term conditions for each land point and became the main clustering dataset.",
            ]),
            {
              name: "levels-bullets",
              width: fill,
              height: hug,
              style: { fontSize: 24, color: INK, breakLine: true },
            },
          ),
        ]),
        column({ name: "right", width: fill, height: hug, gap: 16 }, [
          text("Climate-normal enrichment", {
            name: "enrich-head",
            width: fill,
            height: hug,
            style: { fontSize: 26, bold: true, color: BLUE },
          }),
          text(
            bulletBlock([
              "Interannual variability was added for temperature, rainfall, wind, and cloud cover.",
              "Season-specific signatures were created for temperature, rainfall, humidity, wind, cloud, and solar variables.",
              "Monsoon-sensitive features were added, including monsoon rainfall share, pre-monsoon heat contrast, seasonal humidity contrast, and rainfall seasonality.",
              "These enrichments made the clustering much more meaningful for Indian climate structure.",
            ]),
            {
              name: "enrich-bullets",
              width: fill,
              height: hug,
              style: { fontSize: 24, color: INK, breakLine: true },
            },
          ),
        ]),
      ],
    ),
    { frame: { left: 0, top: 0, width: WIDTH, height: HEIGHT }, baseUnit: 8 },
  );
}

function addModelSlide() {
  const slide = deck.slides.add();
  slide.compose(
    grid(
      {
        name: "model-root",
        width: fill,
        height: fill,
        padding: { x: 88, y: 72 },
        columns: [fr(1), fr(1)],
        rows: [auto, fr(1)],
        columnGap: 40,
        rowGap: 28,
      },
      [
        column({ name: "head", width: fill, height: hug, gap: 18, columnSpan: 2 }, [
          text("Scaling, PCA, and Clustering Model Selection", {
            name: "section",
            width: fill,
            height: hug,
            style: { fontSize: 18, bold: true, color: ACCENT },
          }),
          text("How the final production model was chosen", {
            name: "title",
            width: wrap(1220),
            height: hug,
            style: { fontSize: 50, bold: true, color: INK },
          }),
          rule({ name: "rule", width: fixed(220), stroke: ACCENT, weight: 4 }),
        ]),
        text(
          bulletBlock([
            "All numeric climate-normal features were standardized before clustering.",
            "PCA reduced the feature space while preserving roughly 95% or more of the explained variance.",
            "The project compared K-Means, Hierarchical (Ward and Average), DBSCAN, HDBSCAN, and GMM.",
            "The evaluation considered silhouette score, Calinski-Harabasz, Davies-Bouldin, cluster balance, cluster share, and noise behavior.",
          ]),
          {
            name: "left-bullets",
            width: fill,
            height: hug,
            style: { fontSize: 24, color: INK, breakLine: true },
          },
        ),
        column({ name: "right", width: fill, height: hug, gap: 16 }, [
          text("Why GMM(k=8) was selected", {
            name: "why-head",
            width: fill,
            height: hug,
            style: { fontSize: 26, bold: true, color: BLUE },
          }),
          text(
            bulletBlock([
              "HDBSCAN achieved a high silhouette score but treated too many points as noise for a full India-wide zoning model.",
              "Lower-cluster solutions were too coarse and merged climatically distinct regions.",
              "GMM handled gradual transitions better through probabilistic clustering.",
              "The final GMM(k=8) model gave full coverage and geographically meaningful climate regions.",
            ]),
            {
              name: "why-bullets",
              width: fill,
              height: hug,
              style: { fontSize: 24, color: INK, breakLine: true },
            },
          ),
        ]),
      ],
    ),
    { frame: { left: 0, top: 0, width: WIDTH, height: HEIGHT }, baseUnit: 8 },
  );
}

function addRegionsSlide() {
  const slide = deck.slides.add();
  slide.compose(
    grid(
      {
        name: "regions-root",
        width: fill,
        height: fill,
        padding: { x: 88, y: 72 },
        columns: [fr(1.08), fr(0.92)],
        rows: [auto, fr(1)],
        columnGap: 38,
        rowGap: 28,
      },
      [
        column({ name: "head", width: fill, height: hug, gap: 18, columnSpan: 2 }, [
          text("Final Climate Regions", {
            name: "section",
            width: fill,
            height: hug,
            style: { fontSize: 18, bold: true, color: ACCENT },
          }),
          text("Eight-region climate map produced by the selected GMM model", {
            name: "title",
            width: wrap(1320),
            height: hug,
            style: { fontSize: 50, bold: true, color: INK },
          }),
          rule({ name: "rule", width: fixed(220), stroke: ACCENT, weight: 4 }),
        ]),
        chart({
          name: "cluster-count-chart",
          chartType: "bar",
          width: 1040,
          height: 700,
          config: {
            title: { text: "Cluster point counts" },
            categories: [
              "East-Central Monsoon",
              "Upper Himalayan",
              "Northwest Dry Plains",
              "Northeast Humid Belt",
              "Central Inland Plateau",
              "Gangetic Plains",
              "Southern Peninsular",
              "Western Himalayan",
            ],
            series: [{ name: "Points", values: [135, 49, 139, 89, 231, 222, 200, 88] }],
          },
        }),
        text(
          bulletBlock([
            "Cluster 0 – East-Central Monsoon Corridor",
            "Cluster 1 – Upper Himalayan Cold Pocket",
            "Cluster 2 – Northwest Dry Plains",
            "Cluster 3 – Northeast Humid Belt",
            "Cluster 4 – Central Inland Plateau",
            "Cluster 5 – Gangetic Alluvial Plains",
            "Cluster 6 – Southern Peninsular Belt",
            "Cluster 7 – Western Himalayan Highlands",
          ]),
          {
            name: "regions-list",
            width: fill,
            height: hug,
            style: { fontSize: 23, color: INK, breakLine: true },
          },
        ),
      ],
    ),
    { frame: { left: 0, top: 0, width: WIDTH, height: HEIGHT }, baseUnit: 8 },
  );
}

function addDashboardSlide() {
  const slide = deck.slides.add();
  slide.compose(
    grid(
      {
        name: "dash-root",
        width: fill,
        height: fill,
        padding: { x: 88, y: 72 },
        columns: [fr(1), fr(1)],
        rows: [auto, fr(1)],
        columnGap: 40,
        rowGap: 28,
      },
      [
        column({ name: "head", width: fill, height: hug, gap: 18, columnSpan: 2 }, [
          text("Dashboard and Prediction System", {
            name: "section",
            width: fill,
            height: hug,
            style: { fontSize: 18, bold: true, color: ACCENT },
          }),
          text("How users explore the regions and predict any place", {
            name: "title",
            width: wrap(1260),
            height: hug,
            style: { fontSize: 50, bold: true, color: INK },
          }),
          rule({ name: "rule", width: fixed(220), stroke: ACCENT, weight: 4 }),
        ]),
        column({ name: "left", width: fill, height: hug, gap: 16 }, [
          text("Dashboard sections", {
            name: "sections-head",
            width: fill,
            height: hug,
            style: { fontSize: 26, bold: true, color: BLUE },
          }),
          text(
            bulletBlock([
              "Overview: metric cards, India cluster map, training ranking, cluster point graph, and enhanced charts.",
              "Cluster Explorer: selected cluster map, regional summary, radar chart, correlation heatmap, and sample points.",
              "Domain Insights: Agriculture, Energy, Disaster, and Urban interpretation tabs.",
            ]),
            {
              name: "sections-bullets",
              width: fill,
              height: hug,
              style: { fontSize: 24, color: INK, breakLine: true },
            },
          ),
          text("Main visualization types", {
            name: "vis-head",
            width: fill,
            height: hug,
            style: { fontSize: 26, bold: true, color: BLUE },
          }),
          text(
            "India cluster map, PCA point graph, pie chart, heatmap, box plots, parallel coordinates, radar chart, correlation matrix, and geographic coverage histograms.",
            {
              name: "vis-text",
              width: wrap(760),
              height: hug,
              style: { fontSize: 22, color: INK },
            },
          ),
        ]),
        column({ name: "right", width: fill, height: hug, gap: 16 }, [
          text("Place-based prediction workflow", {
            name: "pred-head",
            width: fill,
            height: hug,
            style: { fontSize: 26, bold: true, color: BLUE },
          }),
          text(
            bulletBlock([
              "User enters a place name.",
              "The place is geocoded to latitude and longitude.",
              "NASA POWER history is fetched for the exact location.",
              "The same cleaning and feature generation pipeline is applied.",
              "Climate normals are computed and projected into the trained PCA space.",
              "The trained cluster model assigns the place to a learned climate region.",
            ]),
            {
              name: "pred-bullets",
              width: fill,
              height: hug,
              style: { fontSize: 23, color: INK, breakLine: true },
            },
          ),
        ]),
      ],
    ),
    { frame: { left: 0, top: 0, width: WIDTH, height: HEIGHT }, baseUnit: 8 },
  );
}

function addConclusionSlide() {
  const slide = deck.slides.add();
  slide.compose(
    grid(
      {
        name: "conclusion-root",
        width: fill,
        height: fill,
        padding: { x: 88, y: 72 },
        columns: [fr(1), fr(1)],
        rows: [auto, fr(1)],
        columnGap: 40,
        rowGap: 28,
      },
      [
        column({ name: "head", width: fill, height: hug, gap: 18, columnSpan: 2 }, [
          text("Conclusion and Project Outcome", {
            name: "section",
            width: fill,
            height: hug,
            style: { fontSize: 18, bold: true, color: ACCENT },
          }),
          text("What this project finally delivers", {
            name: "title",
            width: wrap(1160),
            height: hug,
            style: { fontSize: 50, bold: true, color: INK },
          }),
          rule({ name: "rule", width: fixed(220), stroke: ACCENT, weight: 4 }),
        ]),
        text(
          bulletBlock([
            "An India-wide, data-driven climate regionalization framework built from long-term NASA POWER weather data.",
            "A full pipeline covering data collection, cleaning, feature engineering, climate-normal generation, PCA, clustering, interpretation, and visualization.",
            "A final 8-region climate map selected from multiple unsupervised learning models.",
            "A place-based prediction system that assigns new queried locations to the learned climate regions.",
          ]),
          {
            name: "left-bullets",
            width: fill,
            height: hug,
            style: { fontSize: 24, color: INK, breakLine: true },
          },
        ),
        text(
          bulletBlock([
            "Practical value across agriculture, energy, disaster risk, and urban planning.",
            "A working Streamlit dashboard for exploration and explanation.",
            "A strong foundation for future validation, uncertainty mapping, elevation/coastal enrichment, and temporal stability studies.",
            "Overall, the project moves from raw weather observations to an interpretable national climate intelligence system.",
          ]),
          {
            name: "right-bullets",
            width: fill,
            height: hug,
            style: { fontSize: 24, color: INK, breakLine: true },
          },
        ),
      ],
    ),
    { frame: { left: 0, top: 0, width: WIDTH, height: HEIGHT }, baseUnit: 8 },
  );
}

addCoverSlide();
addProblemSlide();
addDataCollectionSlide();
addPreprocessingSlide();
addFeatureEngineeringSlide();
addAggregationSlide();
addModelSlide();
addRegionsSlide();
addDashboardSlide();
addConclusionSlide();

const outPath = "D:/Collage/Semester 6/Unsuperwised Learning/Project/weather-pattern-clustering/tmp/climate-regionalization-india/output/climate_regionalization_india_10_slide.pptx";
const pptx = await PresentationFile.exportPptx(deck);
await pptx.save(outPath);

console.log(JSON.stringify({ outPath, slideCount: deck.slides.length }, null, 2));
