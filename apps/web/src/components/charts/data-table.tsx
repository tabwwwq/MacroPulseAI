import type { ChartSeries } from "@/components/charts/types";
import { alignSeries } from "@/lib/export";

export interface DataTableProps {
  series: ChartSeries[];
  caption: string;
  height?: number;
}

export function DataTable({ series, caption, height = 280 }: DataTableProps) {
  const { periods, columns } = alignSeries(series);
  return (
    <div
      className="relative overflow-auto rounded-lg border border-line focus-visible:outline-offset-2"
      style={{ maxHeight: height }}
      role="region"
      aria-label={`${caption} table`}
      tabIndex={0}
    >
      <table className="w-full border-collapse text-left text-sm tabular">
        <caption className="sr-only">{caption}</caption>
        <thead className="sticky top-0 bg-surface-2 text-fg-muted">
          <tr>
            <th scope="col" className="whitespace-nowrap px-3 py-2 font-medium">Period</th>
            {columns.map(({ label }, index) => (
              <th key={series[index]?.id ?? index} scope="col" className="px-3 py-2 text-right font-medium">
                {label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {periods.map((period, index) => (
            <tr key={period} className="border-t border-line">
              <th scope="row" className="whitespace-nowrap px-3 py-2 font-normal text-fg-muted">{period}</th>
              {columns.map(({ values }, columnIndex) => (
                <td key={series[columnIndex]?.id ?? columnIndex} className="px-3 py-2 text-right text-fg">
                  {values[index] === null ? <span title="No observation for this period">N/A</span> : values[index]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
