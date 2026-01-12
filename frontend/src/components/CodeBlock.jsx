import React, { useState } from 'react';
import { Check, Copy } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

const CodeBlock = ({ language, value }) => {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(value);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="rounded-lg overflow-hidden my-4 border border-zinc-700 bg-[#1e1e1e] shadow-md">
            <div className="flex items-center justify-between px-4 py-2 bg-[#2d2d2d] border-b border-zinc-700">
                <span className="text-xs font-mono text-zinc-400 lowercase">{language || 'code'}</span>
                <button
                    onClick={handleCopy}
                    className="flex items-center gap-1.5 text-xs text-zinc-400 hover:text-white transition-colors cursor-pointer"
                >
                    {copied ? <Check size={14} className="text-green-400" /> : <Copy size={14} />}
                    {copied ? "Copied!" : "Copy Code"}
                </button>
            </div>
            <div className="text-sm font-mono">
                <SyntaxHighlighter
                    language={language}
                    style={vscDarkPlus}
                    customStyle={{ margin: 0, padding: '1rem', background: 'transparent' }}
                    wrapLongLines={true}
                >
                    {value}
                </SyntaxHighlighter>
            </div>
        </div>
    );
};

export default CodeBlock;
