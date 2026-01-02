import ReactMarkdown from 'react-markdown';
import { AbcRenderer } from './AbcRenderer';

interface MarkdownRendererProps {
    children: string;
    className?: string;
}

export function MarkdownRenderer({ children, className }: MarkdownRendererProps) {
    return (
        <div className={className}>
            <ReactMarkdown
                components={{
                    code({ node, inline, className, children, ...props }: any) {
                        const match = /language-(\w+)/.exec(className || '');
                        const isAbc = match && match[1] === 'abc';

                        if (!inline && isAbc) {
                            return (
                                <div className="my-4 p-4 bg-white border border-neutral-200 rounded-lg shadow-sm overflow-x-auto">
                                    <AbcRenderer notation={String(children).replace(/\n$/, '')} />
                                </div>
                            );
                        }

                        return (
                            <code className={className} {...props}>
                                {children}
                            </code>
                        );
                    },
                    h1: ({ node, ...props }) => <h1 className="text-2xl font-bold mt-6 mb-4 text-neutral-900" {...props} />,
                    h2: ({ node, ...props }) => <h2 className="text-xl font-bold mt-5 mb-3 text-neutral-800 border-b border-neutral-100 pb-2" {...props} />,
                    h3: ({ node, ...props }) => <h3 className="text-lg font-semibold mt-4 mb-2 text-neutral-800" {...props} />,
                    p: ({ node, ...props }) => <p className="mb-4 leading-relaxed text-neutral-700" {...props} />,
                    ul: ({ node, ...props }) => <ul className="list-disc list-inside mb-4 space-y-1 text-neutral-700 ml-4" {...props} />,
                    ol: ({ node, ...props }) => <ol className="list-decimal list-inside mb-4 space-y-1 text-neutral-700 ml-4" {...props} />,
                    li: ({ node, ...props }) => <li className="pl-1 marker:text-neutral-400" {...props} />,
                    blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-orange-200 pl-4 py-1 italic text-neutral-600 bg-neutral-50 rounded-r my-4" {...props} />,
                    a: ({ node, ...props }) => <a className="text-orange-600 hover:text-orange-700 underline underline-offset-2" {...props} />
                }}
            >
                {children}
            </ReactMarkdown>
        </div>
    );
}
