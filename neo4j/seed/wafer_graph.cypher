CREATE CONSTRAINT wafer_id_unique IF NOT EXISTS
FOR (w:Wafer)
REQUIRE w.wafer_id IS UNIQUE;

CREATE CONSTRAINT recipe_id_unique IF NOT EXISTS
FOR (r:Recipe)
REQUIRE r.recipe_id IS UNIQUE;

CREATE CONSTRAINT metrology_id_unique IF NOT EXISTS
FOR (m:Metrology)
REQUIRE m.metrology_id IS UNIQUE;

UNWIND [
  {
    recipe_id: "RCP-LTH-001",
    name: "Critical Lithography",
    process_family: "Lithography",
    tool_id: "LITHO-02",
    chamber: "TRACK-A",
    revision: "A3"
  },
  {
    recipe_id: "RCP-ETC-014",
    name: "Gate Etch Main",
    process_family: "Etch",
    tool_id: "ETCH-07",
    chamber: "C2",
    revision: "B7"
  },
  {
    recipe_id: "RCP-CVD-003",
    name: "Oxide CVD",
    process_family: "Deposition",
    tool_id: "CVD-04",
    chamber: "D1",
    revision: "C1"
  }
] AS recipe_row
MERGE (r:Recipe {recipe_id: recipe_row.recipe_id})
SET
  r.name = recipe_row.name,
  r.process_family = recipe_row.process_family,
  r.tool_id = recipe_row.tool_id,
  r.chamber = recipe_row.chamber,
  r.revision = recipe_row.revision,
  r.dataset = "wafer_demo";

UNWIND [
  {
    wafer_id: "WAF-A1001",
    lot_id: "LOT-A1",
    product: "Logic-7nm",
    line: "FAB-1",
    process_step: "Lithography",
    status: "COMPLETE",
    recipe_id: "RCP-LTH-001"
  },
  {
    wafer_id: "WAF-A1002",
    lot_id: "LOT-A1",
    product: "Logic-7nm",
    line: "FAB-1",
    process_step: "Lithography",
    status: "COMPLETE",
    recipe_id: "RCP-LTH-001"
  },
  {
    wafer_id: "WAF-B2101",
    lot_id: "LOT-B2",
    product: "NAND-176L",
    line: "FAB-2",
    process_step: "Etch",
    status: "COMPLETE",
    recipe_id: "RCP-ETC-014"
  },
  {
    wafer_id: "WAF-B2102",
    lot_id: "LOT-B2",
    product: "NAND-176L",
    line: "FAB-2",
    process_step: "Etch",
    status: "HOLD",
    recipe_id: "RCP-ETC-014"
  },
  {
    wafer_id: "WAF-C3301",
    lot_id: "LOT-C3",
    product: "DRAM-1bnm",
    line: "FAB-3",
    process_step: "Deposition",
    status: "COMPLETE",
    recipe_id: "RCP-CVD-003"
  },
  {
    wafer_id: "WAF-C3302",
    lot_id: "LOT-C3",
    product: "DRAM-1bnm",
    line: "FAB-3",
    process_step: "Deposition",
    status: "REWORK",
    recipe_id: "RCP-CVD-003"
  }
] AS wafer_row
MERGE (w:Wafer {wafer_id: wafer_row.wafer_id})
SET
  w.lot_id = wafer_row.lot_id,
  w.product = wafer_row.product,
  w.line = wafer_row.line,
  w.process_step = wafer_row.process_step,
  w.status = wafer_row.status,
  w.dataset = "wafer_demo"
WITH w, wafer_row
MATCH (r:Recipe {recipe_id: wafer_row.recipe_id})
MERGE (w)-[:USES_RECIPE]->(r);

UNWIND [
  {
    metrology_id: "MET-0001",
    wafer_id: "WAF-A1001",
    metric: "critical_dimension",
    value: 44.8,
    unit: "nm",
    site: "CENTER",
    tool: "CDSEM-02",
    measured_at: "2026-03-18T09:10:00Z"
  },
  {
    metrology_id: "MET-0002",
    wafer_id: "WAF-A1001",
    metric: "overlay",
    value: 2.1,
    unit: "nm",
    site: "EDGE-N",
    tool: "OVL-11",
    measured_at: "2026-03-18T09:12:00Z"
  },
  {
    metrology_id: "MET-0003",
    wafer_id: "WAF-A1002",
    metric: "critical_dimension",
    value: 45.2,
    unit: "nm",
    site: "CENTER",
    tool: "CDSEM-02",
    measured_at: "2026-03-18T09:21:00Z"
  },
  {
    metrology_id: "MET-0004",
    wafer_id: "WAF-A1002",
    metric: "overlay",
    value: 2.4,
    unit: "nm",
    site: "EDGE-S",
    tool: "OVL-11",
    measured_at: "2026-03-18T09:22:00Z"
  },
  {
    metrology_id: "MET-0005",
    wafer_id: "WAF-B2101",
    metric: "etch_depth",
    value: 109.4,
    unit: "nm",
    site: "CENTER",
    tool: "PROFIL-03",
    measured_at: "2026-03-18T10:05:00Z"
  },
  {
    metrology_id: "MET-0006",
    wafer_id: "WAF-B2101",
    metric: "defect_count",
    value: 7,
    unit: "count",
    site: "FULL",
    tool: "KLA-2910",
    measured_at: "2026-03-18T10:07:00Z"
  },
  {
    metrology_id: "MET-0007",
    wafer_id: "WAF-B2102",
    metric: "etch_depth",
    value: 112.9,
    unit: "nm",
    site: "CENTER",
    tool: "PROFIL-03",
    measured_at: "2026-03-18T10:16:00Z"
  },
  {
    metrology_id: "MET-0008",
    wafer_id: "WAF-B2102",
    metric: "defect_count",
    value: 16,
    unit: "count",
    site: "FULL",
    tool: "KLA-2910",
    measured_at: "2026-03-18T10:18:00Z"
  },
  {
    metrology_id: "MET-0009",
    wafer_id: "WAF-C3301",
    metric: "film_thickness",
    value: 698.5,
    unit: "angstrom",
    site: "CENTER",
    tool: "ELLIPS-05",
    measured_at: "2026-03-18T11:02:00Z"
  },
  {
    metrology_id: "MET-0010",
    wafer_id: "WAF-C3301",
    metric: "uniformity",
    value: 1.9,
    unit: "%",
    site: "FULL",
    tool: "ELLIPS-05",
    measured_at: "2026-03-18T11:04:00Z"
  },
  {
    metrology_id: "MET-0011",
    wafer_id: "WAF-C3302",
    metric: "film_thickness",
    value: 706.2,
    unit: "angstrom",
    site: "CENTER",
    tool: "ELLIPS-05",
    measured_at: "2026-03-18T11:16:00Z"
  },
  {
    metrology_id: "MET-0012",
    wafer_id: "WAF-C3302",
    metric: "uniformity",
    value: 3.4,
    unit: "%",
    site: "FULL",
    tool: "ELLIPS-05",
    measured_at: "2026-03-18T11:18:00Z"
  }
] AS metrology_row
MERGE (m:Metrology {metrology_id: metrology_row.metrology_id})
SET
  m.metric = metrology_row.metric,
  m.value = metrology_row.value,
  m.unit = metrology_row.unit,
  m.site = metrology_row.site,
  m.tool = metrology_row.tool,
  m.measured_at = metrology_row.measured_at,
  m.dataset = "wafer_demo"
WITH m, metrology_row
MATCH (w:Wafer {wafer_id: metrology_row.wafer_id})
MERGE (w)-[:HAS_METROLOGY]->(m);
