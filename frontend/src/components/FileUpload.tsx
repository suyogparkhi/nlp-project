import { useState } from 'react';

interface Props {
    onUpload: (files: File[]) => Promise<void>;
}

export default function FileUpload({ onUpload }: Props) {
    const [files, setFiles] = useState<File[]>([]);
    const [uploading, setUploading] = useState(false);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setFiles(Array.from(e.target.files));
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (files.length === 0) return;

        setUploading(true);
        try {
            await onUpload(files);
            setFiles([]);
            alert('Documents uploaded successfully!');
        } catch (error) {
            alert('Upload failed: ' + error);
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="file-upload">
            <h3>Upload Documents</h3>
            <form onSubmit={handleSubmit}>
                <input
                    type="file"
                    multiple
                    accept=".pdf,.doc,.docx,.txt"
                    onChange={handleFileChange}
                    disabled={uploading}
                />
                {files.length > 0 && (
                    <div className="file-list">
                        <p>Selected files:</p>
                        <ul>
                            {files.map((f, i) => <li key={i}>{f.name}</li>)}
                        </ul>
                    </div>
                )}
                <button type="submit" disabled={uploading || files.length === 0}>
                    {uploading ? 'Uploading...' : 'Upload'}
                </button>
            </form>
        </div>
    );
}
