import React, { createContext, useContext, useState, useEffect } from 'react';

const SettingsContext = createContext();

export const useSettings = () => useContext(SettingsContext);

export const SettingsProvider = ({ children }) => {
    // Load from localStorage or defaults
    const [model, setModel] = useState(localStorage.getItem('model') || "llama-3.3-70b-versatile");
    const [systemPrompt, setSystemPrompt] = useState(localStorage.getItem('systemPrompt') || "You are a helpful AI assistant.");
    const [temperature, setTemperature] = useState(parseFloat(localStorage.getItem('temperature')) || 0.7);

    // Persist changes
    useEffect(() => {
        localStorage.setItem('model', model);
        localStorage.setItem('systemPrompt', systemPrompt);
        localStorage.setItem('temperature', temperature);
    }, [model, systemPrompt, temperature]);

    return (
        <SettingsContext.Provider value={{
            model, setModel,
            systemPrompt, setSystemPrompt,
            temperature, setTemperature
        }}>
            {children}
        </SettingsContext.Provider>
    );
};
