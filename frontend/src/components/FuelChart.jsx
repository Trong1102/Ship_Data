import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const FuelChart = ({ data }) => {
    return (
        <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                    dataKey="timestamp"
                    stroke="#94a3b8"
                    tickFormatter={(str) => {
                        try {
                            const date = new Date(str + 'Z'); // Ensure UTC parsing if needed, depending on backend
                            return `${date.getHours()}:${date.getMinutes()}`;
                        } catch (e) { return "" }
                    }}
                />
                <YAxis yAxisId="left" stroke="#0ea5e9" label={{ value: 'Fuel (L/h)', angle: -90, position: 'insideLeft', fill: '#0ea5e9' }} />
                <YAxis yAxisId="right" orientation="right" stroke="#10b981" label={{ value: 'RPM', angle: 90, position: 'insideRight', fill: '#10b981' }} />
                <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#fff' }}
                    itemStyle={{ color: '#e2e8f0' }}
                />
                <Line yAxisId="left" type="monotone" dataKey="fuel_consumption" stroke="#0ea5e9" strokeWidth={2} dot={false} name="Fuel (L/h)" />
                <Line yAxisId="right" type="monotone" dataKey="rpm" stroke="#10b981" strokeWidth={2} dot={false} name="RPM" />
            </LineChart>
        </ResponsiveContainer>
    );
};

export default FuelChart;
