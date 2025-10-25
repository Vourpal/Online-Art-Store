"use client";

import React, { useState } from "react";
import { Switch } from "@/components/ui/switch";

interface UserSwitchProps {
  initialOn?: boolean;
  onLabel?: string;
  offLabel?: string;
}

export default function UserSwitch({
  initialOn = false,
  onLabel = "You are ON",
  offLabel = "You are OFF",
}: UserSwitchProps) {
  const [isOn, setIsOn] = useState(initialOn);

  return (
    <div className="p-4 space-y-4">
      <span className="text-lg font-semibold">{isOn ? onLabel : offLabel}</span>
      <Switch checked={isOn} onCheckedChange={(val) => setIsOn(Boolean(val))} className="ml-4"/>
    </div>
  );
}
