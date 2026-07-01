import * as React from "react";
import * as RechartsPrimitive from "recharts";

import { cn } from "@/lib/utils";

// ── Format helpers ────────────────────────────────────────────────

const FORMATTERS: Record<string, (value: number) => string> = {
  number: (v: number) => v.toLocaleString(),
  currency: (v: number) =>
    new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
    }).format(v),
  percent: (v: number) => `${(v * 100).toFixed(0)}%`,
};

// ── Types ─────────────────────────────────────────────────────────

export type ChartConfig = Record<
  string,
  {
    label: string;
    color?: string;
    icon?: React.ComponentType<{ className?: string }>;
    formatter?: (value: number) => string;
  }
>;

type ChartContextPayload = {
  config: ChartConfig;
};

// ── Context ───────────────────────────────────────────────────────

const ChartContext = React.createContext<ChartContextPayload | null>(null);

function useChart(): ChartContextPayload {
  const ctx = React.useContext(ChartContext);
  if (ctx === null) {
    throw new Error("useChart must be used within a <ChartContainer />");
  }
  return ctx;
}

// ── ChartContainer ────────────────────────────────────────────────

export interface ChartContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  config: ChartConfig;
  /** Recharts ResponsiveContainer `aspect` or `height` prop */
  height?: number;
  aspect?: number;
  children: React.ReactNode;
}

const ChartContainer = React.forwardRef<HTMLDivElement, ChartContainerProps>(
  ({ id, className, children, config, height = 300, aspect, ...props }, ref) => {
    const uniqueId = React.useId();
    const chartId = `chart-${id ?? uniqueId.replace(/:/g, "")}`;

    return (
      <ChartContext.Provider value={{ config }}>
        <div
          data-chart={chartId}
          ref={ref}
          className={cn(
            "flex w-full justify-center text-xs [&_.recharts-cartesian-axis-tick_text]:fill-muted-foreground [&_.recharts-cartesian-grid_line[stroke='#ccc']]:stroke-border/50 [&_.recharts-curve.recharts-tooltip-cursor]:stroke-border [&_.recharts-polar-grid_[stroke='#ccc']]:stroke-border [&_.recharts-radial-bar-background-sector]:fill-muted [&_.recharts-rectangle.recharts-tooltip-cursor]:fill-muted [&_.recharts-reference-line_[stroke='#ccc']]:stroke-border",
            className,
          )}
          style={{ height: typeof height === "number" ? `${height}px` : height }}
          {...props}
        >
          <RechartsPrimitive.ResponsiveContainer width="100%" height="100%" aspect={aspect}>
            {children}
          </RechartsPrimitive.ResponsiveContainer>
        </div>
      </ChartContext.Provider>
    );
  },
);
ChartContainer.displayName = "ChartContainer";

// ── CSS variable bridge — sets --color-{key} on the chart container ──

function ChartStyle({ id, config }: { id: string; config: ChartConfig }): React.ReactElement {
  const css = Object.entries(config)
    .filter(([, entry]) => Boolean(entry.color))
    .map(([key, entry]) => `--color-${key}: ${entry.color};`)
    .join("\n");
  return (
    <style
      dangerouslySetInnerHTML={{
        __html: `[data-chart="${id}"] {\n${css}\n}`,
      }}
    />
  );
}

// ── Re-export recharts elements with proper typing ────────────────

// Strongly-typed re-exports. Using `ComponentProps<typeof X>` keeps full
// recharts types but lets us forward refs consistently with our pattern.
export const Bar = (
  props: React.ComponentProps<typeof RechartsPrimitive.Bar>,
): React.ReactElement => <RechartsPrimitive.Bar {...props} />;
Bar.displayName = "Chart.Bar";

export const BarChart = (
  props: React.ComponentProps<typeof RechartsPrimitive.BarChart>,
): React.ReactElement => <RechartsPrimitive.BarChart {...props} />;
BarChart.displayName = "Chart.BarChart";

export const Line = (
  props: React.ComponentProps<typeof RechartsPrimitive.Line>,
): React.ReactElement => <RechartsPrimitive.Line {...props} />;
Line.displayName = "Chart.Line";

export const LineChart = (
  props: React.ComponentProps<typeof RechartsPrimitive.LineChart>,
): React.ReactElement => <RechartsPrimitive.LineChart {...props} />;
LineChart.displayName = "Chart.LineChart";

export const Area = (
  props: React.ComponentProps<typeof RechartsPrimitive.Area>,
): React.ReactElement => <RechartsPrimitive.Area {...props} />;
Area.displayName = "Chart.Area";

export const AreaChart = (
  props: React.ComponentProps<typeof RechartsPrimitive.AreaChart>,
): React.ReactElement => <RechartsPrimitive.AreaChart {...props} />;
AreaChart.displayName = "Chart.AreaChart";

export const Pie = (
  props: React.ComponentProps<typeof RechartsPrimitive.Pie>,
): React.ReactElement => <RechartsPrimitive.Pie {...props} />;
Pie.displayName = "Chart.Pie";

export const PieChart = (
  props: React.ComponentProps<typeof RechartsPrimitive.PieChart>,
): React.ReactElement => <RechartsPrimitive.PieChart {...props} />;
PieChart.displayName = "Chart.PieChart";

export const Cell = (
  props: React.ComponentProps<typeof RechartsPrimitive.Cell>,
): React.ReactElement => <RechartsPrimitive.Cell {...props} />;
Cell.displayName = "Chart.Cell";

export const XAxis = (
  props: React.ComponentProps<typeof RechartsPrimitive.XAxis>,
): React.ReactElement => <RechartsPrimitive.XAxis {...props} />;
XAxis.displayName = "Chart.XAxis";

export const YAxis = (
  props: React.ComponentProps<typeof RechartsPrimitive.YAxis>,
): React.ReactElement => <RechartsPrimitive.YAxis {...props} />;
YAxis.displayName = "Chart.YAxis";

export const CartesianGrid = (
  props: React.ComponentProps<typeof RechartsPrimitive.CartesianGrid>,
): React.ReactElement => <RechartsPrimitive.CartesianGrid {...props} />;
CartesianGrid.displayName = "Chart.CartesianGrid";

export const ResponsiveContainer = RechartsPrimitive.ResponsiveContainer;

// ── Tooltip ────────────────────────────────────────────────────────

export interface ChartTooltipContentProps extends React.HTMLAttributes<HTMLDivElement> {
  active?: boolean;
  payload?: ReadonlyArray<{
    name?: string | number;
    value?: number | string;
    payload?: Record<string, unknown>;
    color?: string;
    dataKey?: string;
  }>;
  label?: string | number;
  labelFormatter?: (label: string | number) => React.ReactNode;
  valueFormatter?: (value: number) => string;
  hideLabel?: boolean;
  nameKey?: string;
  labelKey?: string;
  indicator?: "line" | "dot" | "dashed";
}

export function ChartTooltipContent({
  active,
  payload,
  label,
  labelFormatter,
  valueFormatter,
  hideLabel = false,
  nameKey,
  labelKey,
  indicator = "dot",
  className,
  ...rest
}: ChartTooltipContentProps): React.ReactElement | null {
  const { config } = useChart();

  if (!active || !payload || payload.length === 0) {
    return null;
  }

  const tooltipLabel = React.useMemo(() => {
    if (hideLabel || label === undefined || label === null) return null;
    const item = payload[0];
    const key = `${labelKey ?? item?.dataKey ?? item?.name ?? "value"}`;
    const itemConfig = config[key];
    const value =
      !labelKey && typeof label === "string" ? (config[label]?.label ?? label) : itemConfig?.label;
    if (labelFormatter && typeof label === "string") {
      return labelFormatter(label);
    }
    return value;
  }, [label, labelFormatter, payload, hideLabel, labelKey, config]);

  return (
    <div
      className={cn(
        "grid min-w-[8rem] items-start gap-1.5 rounded-lg border border-border/50 bg-background px-2.5 py-1.5 text-xs shadow-xl",
        className,
      )}
      {...rest}
    >
      {tooltipLabel ? <div className="font-medium">{tooltipLabel}</div> : null}
      <div className="grid gap-1.5">
        {payload.map((item, index) => {
          const key = `${nameKey ?? item.name ?? item.dataKey ?? "value"}`;
          const itemConfig = config[key];
          const indicatorColor = item.color ?? `var(--color-${key})`;
          const formatter = itemConfig?.formatter ?? valueFormatter;
          const displayValue =
            typeof item.value === "number"
              ? formatter
                ? formatter(item.value)
                : item.value.toLocaleString()
              : item.value;
          return (
            <div
              key={`${item.dataKey ?? item.name ?? index}`}
              className="flex w-full items-center gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 [&>svg]:text-muted-foreground"
            >
              {indicator === "dot" ? (
                <span
                  className="h-2.5 w-2.5 shrink-0 rounded-[2px]"
                  style={{ backgroundColor: indicatorColor }}
                />
              ) : indicator === "line" ? (
                <span className="h-0.5 w-3 shrink-0" style={{ backgroundColor: indicatorColor }} />
              ) : (
                <span
                  className="h-0.5 w-3 shrink-0 border-dashed"
                  style={{ borderTop: `2px dashed ${indicatorColor}` }}
                />
              )}
              <span className="flex flex-1 items-center justify-between gap-2 leading-none">
                <span className="text-muted-foreground">{itemConfig?.label ?? item.name}</span>
                <span className="font-mono font-medium tabular-nums text-foreground">
                  {displayValue}
                </span>
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export const ChartTooltip = (
  props: React.ComponentProps<typeof RechartsPrimitive.Tooltip>,
): React.ReactElement => {
  // Recharts v3 Tooltip forwards its own ref; we just pass through with
  // our default content wrapper. Consumers can pass content={<ChartTooltipContent />}.
  return <RechartsPrimitive.Tooltip {...props} />;
};
ChartTooltip.displayName = "ChartTooltip";

// ── Legend ─────────────────────────────────────────────────────────

export interface ChartLegendContentProps extends React.HTMLAttributes<HTMLDivElement> {
  payload?: ReadonlyArray<{
    value?: string;
    color?: string;
    dataKey?: string;
  }>;
  verticalAlign?: "top" | "middle" | "bottom";
  hideIcon?: boolean;
  nameKey?: string;
}

export function ChartLegendContent({
  payload,
  verticalAlign = "bottom",
  hideIcon = false,
  nameKey,
  className,
  ...rest
}: ChartLegendContentProps): React.ReactElement | null {
  const { config } = useChart();
  if (!payload || payload.length === 0) return null;

  return (
    <div
      className={cn(
        "flex items-center justify-center gap-4",
        verticalAlign === "top" ? "pb-3" : "pt-3",
        className,
      )}
      {...rest}
    >
      {payload.map((item) => {
        const key = `${nameKey ?? item.dataKey ?? "value"}`;
        const itemConfig = config[key];
        return (
          <div
            key={`${item.value ?? key}`}
            className="flex items-center gap-1.5 [&>svg]:h-3 [&>svg]:w-3 [&>svg]:text-muted-foreground"
          >
            {itemConfig?.icon ? (
              <itemConfig.icon className="h-3 w-3" />
            ) : hideIcon ? null : (
              <span
                className="h-2 w-2 shrink-0 rounded-[2px]"
                style={{ backgroundColor: item.color }}
              />
            )}
            {itemConfig?.label ?? item.value}
          </div>
        );
      })}
    </div>
  );
}

export const ChartLegend = (
  props: React.ComponentProps<typeof RechartsPrimitive.Legend>,
): React.ReactElement => <RechartsPrimitive.Legend {...props} />;
ChartLegend.displayName = "ChartLegend";

// ── Convenience helper for series arrays ─────────────────────────

/**
 * Build a ChartConfig from a series spec. Pure helper so callers don't
 * have to hand-roll the config object.
 */
export function buildChartConfig(
  series: ReadonlyArray<{
    key: string;
    label: string;
    color?: string;
    formatter?: keyof typeof FORMATTERS;
  }>,
): ChartConfig {
  const config: ChartConfig = {};
  for (const s of series) {
    config[s.key] = {
      label: s.label,
      color: s.color,
      formatter: s.formatter ? FORMATTERS[s.formatter] : undefined,
    };
  }
  return config;
}
