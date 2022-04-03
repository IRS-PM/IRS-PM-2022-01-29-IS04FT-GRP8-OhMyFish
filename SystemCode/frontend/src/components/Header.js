import PropTypes from "prop-types";
import { useLocation } from "react-router-dom";
import Button from "./Button";

const Header = ({ caseId }) => {
  return (
    <div className="lc-header">
      <div className="lc-headerbox">
        <div>
          <h1 aria-expanded="true" className="lc-headertitle">
            Welcome to OhMyFish {caseId}
          </h1>
        </div>
      </div>
    </div>
  );
};

export default Header;