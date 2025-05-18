import { useState, useEffect } from "react";
import axios from "axios";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  LineChart,
  Line
} from "recharts";
import PowerBIEmbed from "./PowerBIEmbed";
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const COLORS = ["#FF4C4C", "#00C49F"]; // High Risk, Low Risk

function App() {
  const [weatherData, setWeatherData] = useState([]);
  const [pieData, setPieData] = useState([]);
  const [selectedChart, setSelectedChart] = useState("pie");
  const [searchTerm, setSearchTerm] = useState("");
  const [activeView, setActiveView] = useState(""); // "", "weather", "chart", "powerbi"

  useEffect(() => {
    if (activeView === "weather") {
      axios.get("/api/weather").then((res) => {
        setWeatherData(res.data);
        // Check for high-risk cities and show toasts
      res.data.forEach((row) => {
        if (row.risk_level === "High Risk") {
          toast.error(`⚠️ High Risk Alert in ${row.city}!`, {
            position: "top-right",
            autoClose: 5000,
            hideProgressBar: false,
            closeOnClick: true,
            pauseOnHover: true,
            draggable: true
          });
        }
      });
    });
    } else if (activeView === "chart") {
      axios.get("/api/stats").then((res) => {
        const formattedData = Object.entries(res.data).map(([name, value]) => ({
          name,
          value,
        }));
        setPieData(formattedData);
      });
    }
  }, [activeView]);

  const filteredData = weatherData.filter((row) =>
    row.city.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div
      className="min-h-screen bg-cover bg-center"
    >
      <div className="bg-black bg-opacity-70 min-h-screen text-white px-6 py-10">
      <h1 className="text-4xl font-bold mb-6 flex items-center text-center text-white animate-glow drop-shadow-lg"><center>
        🌩️ <span className="ml-2">Cloudburst Risk Dashboard</span></center>
      </h1>
      <div className="rain-overlay"></div>
      <div className="lightning-overlay"></div>


        {/* Navigation Buttons */}
        <div className="flex justify-start mb-8">
        <div className="flex space-x-4">
        <button
          onClick={() => setActiveView("weather")}
          className={`px-5 py-2 rounded-lg font-semibold transition duration-300 ${
            activeView === "weather"
              ? "bg-white text-black shadow-md"
              : "bg-gray-700 hover:bg-gray-600"
          }`}
        >
          Live Weather
        </button>
        <button
          onClick={() => setActiveView("chart")}
          className={`px-5 py-2 rounded-lg font-semibold transition duration-300 ${
            activeView === "chart"
              ? "bg-white text-black shadow-md"
              : "bg-gray-700 hover:bg-gray-600"
          }`}
        >
          Risk Chart
        </button>
        <button
          onClick={() => setActiveView("powerbi")}
          className={`px-5 py-2 rounded-lg font-semibold transition duration-300 ${
            activeView === "powerbi"
              ? "bg-white text-black shadow-md"
              : "bg-gray-700 hover:bg-gray-600"
          }`}
        >
          Power BI Report
        </button>
        </div>
        </div>
        
        {/* Conditional Rendering with fade-in animation */}
        {activeView === "weather" && (
          <div className="fade-in">
            <h2 className="text-2xl font-semibold mb-4">Live Weather & Risk</h2>
            <input
              type="text"
              placeholder="Search city..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="mb-4 p-2 w-60 rounded text-black"
            />
            <div className="overflow-x-auto">
              <table className="table-auto w-full border-collapse rounded-lg overflow-hidden">
                <thead className="bg-gray-700 text-white">
                  <tr>
                    <th className="px-4 py-2">City</th>
                    <th className="px-4 py-2">Timestamp</th>
                    <th className="px-4 py-2">Temp (°C)</th>
                    <th className="px-4 py-2">Humidity (%)</th>
                    <th className="px-4 py-2">Pressure (hPa)</th>
                    <th className="px-4 py-2">Wind (m/s)</th>
                    <th className="px-4 py-2">Cloudiness (%)</th>
                    <th className="px-4 py-2">Risk Level</th>
                    <th className="px-4 py-2">Prediction Score</th>
                  </tr>
                </thead>
                <tbody className="text-white">
                  {filteredData.map((row, index) => (
                    <tr key={index} className="border-b border-gray-700">
                      <td className="px-4 py-2">{row.city}</td>
                      <td className="px-4 py-2">{new Date(row.timestamp).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })}</td>
                      <td className="px-4 py-2">{row.temperature}</td>
                      <td className="px-4 py-2">{row.humidity}</td>
                      <td className="px-4 py-2">{row.pressure}</td>
                      <td className="px-4 py-2">{row.wind_speed}</td>
                      <td className="px-4 py-2">{row.cloudiness}</td>
                      <td className="px-4 py-2">{row.risk_level}</td>
                      <td className="px-4 py-2">{row.prediction_score}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeView === "chart" && (
          <div className="fade-in bg-gray-800 p-6 shadow-xl rounded-2xl max-w-5xl mx-auto">
            <h2 className="text-2xl font-bold text-white mb-4 text-center">Risk Visualization</h2>

            {/* Chart Type Buttons */}
            <div className="flex justify-center mb-6 space-x-4">
              <button
                  onClick={() => setSelectedChart("pie")}
                  className={`px-4 py-2 rounded-lg ${
                    selectedChart === "pie" ? "bg-blue-600 text-white" : "bg-gray-200"
                  }`}
              >
                Pie Chart
              </button>
              <button
                onClick={() => setSelectedChart("bar")}
                className={`px-4 py-2 rounded-lg ${
                  selectedChart === "bar" ? "bg-blue-600 text-white" : "bg-gray-200"
                }`}
              >
                Bar Chart
              </button>
              <button
                  onClick={() => setSelectedChart("line")}
                  className={`px-4 py-2 rounded-lg ${
                    selectedChart === "line" ? "bg-blue-600 text-white" : "bg-gray-200"
                  }`}
              >
                Line Chart
              </button>
            </div>

            {/* Chart Render Logic */}
            {selectedChart === "pie" && (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    outerRadius={120}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}

            {selectedChart === "bar" && (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={pieData}>
                  <XAxis dataKey="name" stroke="#fff" />
                  <YAxis stroke="#fff" />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="value" fill="#00C49F" />
                </BarChart>
              </ResponsiveContainer>
            )}

            {selectedChart === "line" && (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={pieData}>
                    <XAxis dataKey="name" stroke="#fff" />
                    <YAxis stroke="#fff" />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="value" stroke="#FF4C4C" />
                </LineChart>
             </ResponsiveContainer>
            )}
          </div>
        )}

        {activeView === "powerbi" && (
          <div className="fade-in mt-6">
            <PowerBIEmbed />
          </div>
        )}
      </div>
      <ToastContainer />
    </div>
  );
}

export default App;
