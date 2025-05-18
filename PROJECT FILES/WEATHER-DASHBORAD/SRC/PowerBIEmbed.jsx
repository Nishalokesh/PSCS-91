import React from "react";
import { motion } from "framer-motion";

const PowerBIEmbed = () => {
  return (
    <motion.div
      className="w-full flex justify-center mt-10 px-4"
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="powerbi-report">
        <iframe
          title="Power BI Report"
          width="100%"
          height="100%"
          src="https://app.powerbi.com/reportEmbed?reportId=150b84bb-d793-4ea5-9e45-70b3812a5ed5&autoAuth=true&ctid=bf93bb5e-ecf0-4e3d-be0e-79b5cc527a48"
          frameBorder="0"
          allowFullScreen={true}
          className="rounded-2xl"
        ></iframe>
      </div>
    </motion.div>
  );
};

export default PowerBIEmbed;
