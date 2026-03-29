'use client'
import { IblaiProviders } from "@/providers/iblai-providers";
import {useEffect, useState} from "react";
export default function Home() {
  const [username, setUsername] = useState(null)
  useEffect(() => {
    setUsername(JSON.parse(localStorage.getItem("userData")).user_nicename)
  })
  return (
    <>
    <IblaiProviders>
      <h1>Your username is: { username }</h1>   
    </IblaiProviders>
    </>
  );
}
