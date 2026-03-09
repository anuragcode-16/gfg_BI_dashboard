// src/components/ChartRenderer.jsx
import {
    BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
    ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, Legend,
} from 'recharts';

const COLORS = ['#9560EB', '#FF69B4', '#7C3AED', '#A78BFA', '#F472B6', '#818CF8'];

const tooltipStyle = {
    backgroundColor: 'rgba(10, 10, 10, 0.95)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '8px',
    color: '#fff',
    fontSize: '0.82rem',
    fontFamily: 'Inter, sans-serif',
};

function DataTable({ data, columns }) {
    if (!data || !data.length) return null;
    const cols = columns || Object.keys(data[0]);
    return (
        <div className="data-table-wrapper">
            <table className="data-table">
                <thead>
                    <tr>{cols.map(c => <th key={c}>{c}</th>)}</tr>
                </thead>
                <tbody>
                    {data.slice(0, 50).map((row, i) => (
                        <tr key={i}>{cols.map(c => <td key={c}>{row[c]}</td>)}</tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

function MetricDisplay({ data, columns }) {
    if (!data || !data.length) return null;
    const cols = columns || Object.keys(data[0]);
    return (
        <div className="metric-display">
            <div className="metric-value">{String(data[0][cols[cols.length - 1]])}</div>
            <div className="metric-label">{cols[cols.length - 1]}</div>
        </div>
    );
}

function formatTick(v) {
    if (typeof v === 'number') {
        if (Math.abs(v) >= 1e9) return (v / 1e9).toFixed(1) + 'B';
        if (Math.abs(v) >= 1e6) return (v / 1e6).toFixed(1) + 'M';
        if (Math.abs(v) >= 1e3) return (v / 1e3).toFixed(1) + 'K';
        return v.toFixed?.(1) ?? v;
    }
    return v;
}

export default function ChartRenderer({ data, columns, visualization }) {
    if (!data || !data.length || !visualization) return null;

    const { chart_type, title, x_axis, y_axis, explanation } = visualization;
    const cols = columns || Object.keys(data[0]);

    // Single metric
    if (data.length === 1 && cols.length <= 2 && chart_type !== 'pie') {
        return (
            <div className="chart-container">
                {title && <div className="chart-title">{title}</div>}
                <MetricDisplay data={data} columns={cols} />
                {explanation && <div className="chart-explanation">{explanation}</div>}
            </div>
        );
    }

    const xKey = x_axis && cols.includes(x_axis) ? x_axis : cols[0];
    const yKey = y_axis && cols.includes(y_axis) ? y_axis : cols.length > 1 ? cols[1] : cols[0];

    const renderChart = () => {
        switch (chart_type) {
            case 'bar':
                return (
                    <ResponsiveContainer width="100%" height={380}>
                        <BarChart data={data} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                            <XAxis dataKey={xKey} tick={{ fill: '#aaa', fontSize: 11 }} angle={-25} textAnchor="end" height={60} />
                            <YAxis tick={{ fill: '#aaa', fontSize: 11 }} tickFormatter={formatTick} />
                            <Tooltip contentStyle={tooltipStyle} formatter={(v) => formatTick(v)} />
                            <Bar dataKey={yKey} radius={[6, 6, 0, 0]} maxBarSize={50}>
                                {data.map((_, i) => (
                                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                );

            case 'line':
                return (
                    <ResponsiveContainer width="100%" height={380}>
                        <LineChart data={data} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                            <XAxis dataKey={xKey} tick={{ fill: '#aaa', fontSize: 11 }} />
                            <YAxis tick={{ fill: '#aaa', fontSize: 11 }} tickFormatter={formatTick} />
                            <Tooltip contentStyle={tooltipStyle} formatter={(v) => formatTick(v)} />
                            <Line
                                type="monotone" dataKey={yKey} stroke="#9560EB" strokeWidth={2.5}
                                dot={{ r: 5, fill: '#000', stroke: '#9560EB', strokeWidth: 2 }}
                                activeDot={{ r: 7, fill: '#9560EB', stroke: '#fff', strokeWidth: 2 }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                );

            case 'pie':
                return (
                    <ResponsiveContainer width="100%" height={380}>
                        <PieChart>
                            <Pie
                                data={data} dataKey={yKey} nameKey={xKey}
                                cx="50%" cy="50%" outerRadius={130} innerRadius={70}
                                paddingAngle={2} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                labelLine={{ stroke: 'rgba(255,255,255,0.2)' }}
                            >
                                {data.map((_, i) => (
                                    <Cell key={i} fill={COLORS[i % COLORS.length]} stroke="#000" strokeWidth={2} />
                                ))}
                            </Pie>
                            <Tooltip contentStyle={tooltipStyle} />
                            <Legend wrapperStyle={{ color: '#aaa', fontSize: '0.8rem' }} />
                        </PieChart>
                    </ResponsiveContainer>
                );

            case 'scatter':
                return (
                    <ResponsiveContainer width="100%" height={380}>
                        <ScatterChart margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                            <XAxis dataKey={xKey} tick={{ fill: '#aaa', fontSize: 11 }} name={xKey} />
                            <YAxis dataKey={yKey} tick={{ fill: '#aaa', fontSize: 11 }} name={yKey} tickFormatter={formatTick} />
                            <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={tooltipStyle} />
                            <Scatter data={data} fill="#9560EB">
                                {data.map((_, i) => (
                                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                                ))}
                            </Scatter>
                        </ScatterChart>
                    </ResponsiveContainer>
                );

            default:
                return <DataTable data={data} columns={cols} />;
        }
    };

    return (
        <div className="chart-container">
            {title && <div className="chart-title">{title}</div>}
            {renderChart()}
            {explanation && <div className="chart-explanation">{explanation}</div>}
        </div>
    );
}
