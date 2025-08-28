import React from 'react';
import Icon from 'react-native-vector-icons/MaterialIcons';

interface IconWrapperProps {
  name: string;
  size?: number;
  color?: string;
  style?: any;
}

const IconWrapper: React.FC<IconWrapperProps> = ({ name, size = 24, color = '#000', style }) => {
  return (
    <Icon 
      name={name} 
      size={size} 
      color={color} 
      style={style}
    />
  );
};

export default IconWrapper;
