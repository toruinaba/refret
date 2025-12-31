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
                    }
                }}
            >
                {children}
            </ReactMarkdown>
        </div>
    );
}
