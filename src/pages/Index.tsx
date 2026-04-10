import { useState, useEffect, useRef } from "react";
import AppShell from "@/components/analyzer/AppShell";
import TabContent from "@/components/analyzer/TabContent";

export default function Index() {
  const [activeTab, setActiveTab] = useState("overview");
  const [scanning, setScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const [scanDone, setScanDone] = useState(true);
  const scanRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startScan = () => {
    if (scanning) return;
    setScanDone(false);
    setScanning(true);
    setScanProgress(0);
    let p = 0;
    scanRef.current = setInterval(() => {
      p += Math.random() * 7 + 2;
      if (p >= 100) {
        p = 100;
        clearInterval(scanRef.current!);
        setScanning(false);
        setScanDone(true);
      }
      setScanProgress(Math.round(p));
    }, 80);
  };

  useEffect(() => () => { if (scanRef.current) clearInterval(scanRef.current); }, []);

  return (
    <AppShell
      activeTab={activeTab}
      setActiveTab={setActiveTab}
      scanning={scanning}
      scanProgress={scanProgress}
      scanDone={scanDone}
      onStartScan={startScan}
    >
      <TabContent activeTab={activeTab} />
    </AppShell>
  );
}
