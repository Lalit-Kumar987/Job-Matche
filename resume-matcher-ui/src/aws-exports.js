// src/aws-exports.js
const awsmobile = {
  Auth: {
    Cognito: {
        region: `${import.meta.env.VITE_AWS_REGION}`,
        userPoolId: `${import.meta.env.VITE_COGNITO_USERPOOL_ID}`,
        userPoolClientId: `${import.meta.env.VITE_COGNITO_CLIENTID}`,
        authenticationFlowType: 'USER_PASSWORD_AUTH',
        authenticationFlowType: 'USER_PASSWORD_AUTH',
    }
  },
};

export default awsmobile;