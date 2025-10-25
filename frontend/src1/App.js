import React, { useEffect, useState } from "react";
import io from "socket.io-client";

const socket = io("http://localhost:5000"); // Flask backend

function App() {
  const [data, setData] = useState(null);

  useEffect(() => {
    socket.on("telemetry", (msg) => setData(msg));
    return () => socket.off("telemetry");
  }, []);

  return (
    <div style={{ padding: "2rem", fontFamily: "Arial" }}>
      <h1>MQTT Telemetry Dashboard</h1>
      {data ? (
        <pre>{JSON.stringify(data, null, 2)}</pre>
      ) : (
        <p>Waiting for telemetry data...</p>
      )}
    </div>
  );
}

export default App;
