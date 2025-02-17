import React from 'react';

const PDFViewer = ({ pdfUrl }) => {
  return (
    <div>
      <object
        data={pdfUrl}
        type="application/pdf"
        width="100%"
        height="600px"
      >
        <p>Unable to display PDF file. <a href={pdfUrl}>Download</a> instead.</p>
      </object>
    </div>
  );
};

export default PDFViewer;
