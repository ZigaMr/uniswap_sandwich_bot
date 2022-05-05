object "Token" {
    code {
        // Store the creator in slot zero.

        // Deploy the contract
        datacopy(0, dataoffset("runtime"), datasize("runtime"))
        return(0, datasize("runtime"))
    }
    object "runtime" {
        code {
            // Protection against sending Ether
            
            // Dispatcher
            switch selector()
            case 0x00 /* "buy token-weth 3gas" */ {
                if gt(number(),shr(0xe8, calldataload(1))){
                    revert(0,0)
                }
                mstore(0,0xa9059cbb00000000000000000000000000000000000000000000000000000000) //Transfer 
                mstore(0x04, shr(0x60, calldataload(0x20)))//Recepient 
                mstore(0x24, shr(0x90, calldataload(0x04)))//Amount
                let success := call(3000000, 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2, 0x00, 0, 0x44, 0, 0x20) // Send the first WETH to the pair
                mstore(0, 0x022c0d9f00000000000000000000000000000000000000000000000000000000)//Sig
                mstore(0x04, shr(0x90, calldataload(0x12)))//Amount
                mstore(0x24, 0x00)//Amount
                mstore(0x44, 0xC6a257797dDD6818840b560C8ab3c6)
                mstore(0x64, 0x80)
                mstore(0x84, 0x00)
                mstore(0xa4, 0x00)
                success := call(3000000, shr(0x60, calldataload(0x20)), 0x00, 0, 0xc4, 0, 0x20) // Call swap
                success := call(3000000, shr(0x60, calldataload(0x34)), 0x00, 0x00, 0x00, 0, 0x20) // Send the first WETH to the pair
                success := call(3000000, shr(0x60, calldataload(0x48)), 0x00, 0x00, 0x00, 0, 0x20) // Send the first WETH to the pair
                success := call(3000000, shr(0x60, calldataload(0x5c)), 0x00, 0x00, 0x00, 0, 0x20) // Send the first WETH to the pair
            }
            case 0x01 /* "buy weth-token 3gas" */ {
                if gt(number(),shr(0xe8, calldataload(1))){
                    revert(0,0)
                }                
                mstore(0,0xa9059cbb00000000000000000000000000000000000000000000000000000000) //Transfer 
                mstore(0x04, shr(0x60, calldataload(0x20)))//Recepient 
                mstore(0x24, shr(0x90, calldataload(0x04)))//Amount
                let success := call(3000000, 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2, 0x00, 0, 0x44, 0, 0x20) // Send the first WETH to the pair
                mstore(0, 0x022c0d9f00000000000000000000000000000000000000000000000000000000)//Sig
                mstore(0x04, 0x00)//Amount
                mstore(0x24, shr(0x90, calldataload(0x12)))//Amount
                mstore(0x44, 0xC6a257797dDD6818840b560C8ab3c6)
                mstore(0x64, 0x80)
                mstore(0x84, 0x00)
                mstore(0xa4, 0x00)
                success := call(3000000, shr(0x60, calldataload(0x20)), 0x00, 0, 0xc4, 0, 0x20) // swap
                success := call(3000000, shr(0x60, calldataload(0x34)), 0x00, 0x00, 0x00, 0, 0x20) // Send the first WETH to the pair
                success := call(3000000, shr(0x60, calldataload(0x48)), 0x00, 0x00, 0x00, 0, 0x20) // Send the first WETH to the pair
                success := call(3000000, shr(0x60, calldataload(0x5c)), 0x00, 0x00, 0x00, 0, 0x20) // Send the first WETH to the pair
                
            }
            case 0x02 /* "sell weth-token 3gas" */ {
                if gt(number(),shr(0xe8, calldataload(1))){
                    revert(0,0)
                }                
                mstore(0x00,0xa9059cbb00000000000000000000000000000000000000000000000000000000) //Transfer 
                mstore(0x04, shr(0x60, calldataload(0x20)))//Recepient 0x6f9E023c0881eC3d8F56630A6C4FD137C025419e
                mstore(0x24, shr(0x90, calldataload(0x12)))//Amount
                let success := call(3000000, shr(0x60, calldataload(0x34)), 0x00, 0, 0x44, 0, 0x20) // Send the first WETH to the pair
                mstore(0, 0x022c0d9f00000000000000000000000000000000000000000000000000000000)//Sig
                mstore(0x04, shr(0x90, calldataload(0x04)))//Amount2
                mstore(0x24, 0x0000000000000000000000000000000000000000000000000000000000000000)//Amount1
                mstore(0x44, 0x0000000000000000000000000000000000c6a257797ddd6818840b560c8ab3c6)
                mstore(0x64, 0x0000000000000000000000000000000000000000000000000000000000000080)
                mstore(0x84, 0x0000000000000000000000000000000000000000000000000000000000000000)
                mstore(0xa4, 0x0000000000000000000000000000000000000000000000000000000000000000)
                success := call(3000000, shr(0x60, calldataload(0x20)), 0x00, 0, 0xc4, 0, 0xc4) // Swap to Weth
                mstore(0x00, 0x70a0823100000000000000000000000000000000000000000000000000000000)
                mstore(0x04, 0x0000000000000000000000000000000000C6a257797dDD6818840b560C8ab3c6)
                success := call(3000000, 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2, 0x00, 0, 0x24, 0, 0x20) // Check WETH balance of this contract
                //log1(0x00, 0xa0, success)
                if lt(mload(0x00), shr(0x90, calldataload(0x48))){
                    //If balance less than passed balance, revert
                    revert(0,0)
                }
                success := call(3000000, shr(0x60, calldataload(0x56)), 0x00, 0x00, 0x00, 0, 0x20) // Send the first WETH to the pair
                success := call(3000000, shr(0x60, calldataload(0x6a)), 0x00, 0x00, 0x00, 0, 0x20) // Send the first WETH to the pair
                success := call(3000000, shr(0x60, calldataload(0x7e)), 0x00, 0x00, 0x00, 0, 0x20) // Send the first WETH to the pair
                //success := call(1000000, coinbase(), callvalue(), 0x00, 0x00, 0, 0x20)
            }
            case 0x03 /* "sell token-weth 3gas" */ {
                if gt(number(),shr(0xe8, calldataload(1))){
                    revert(0,0)
                }
                mstore(0x00,0xa9059cbb00000000000000000000000000000000000000000000000000000000) //Transfer 
                mstore(0x04, shr(0x60, calldataload(0x20)))//Recepient 0x6f9E023c0881eC3d8F56630A6C4FD137C025419e
                mstore(0x24, shr(0x90, calldataload(0x12)))//Amount
                let success := call(3000000, shr(0x60, calldataload(0x34)), 0x00, 0, 0x44, 0, 0x20) // Send the first WETH to the pair
                mstore(0, 0x022c0d9f00000000000000000000000000000000000000000000000000000000)//Sig
                mstore(0x04, 0x00)//Amount1
                mstore(0x24, shr(0x90, calldataload(0x04)))//Amount2
                mstore(0x44, 0xc6a257797ddd6818840b560c8ab3c6)
                mstore(0x64, 0x00)
                mstore(0x84, 0x00)
                mstore(0xa4, 0x00)
                success := call(3000000, shr(0x60, calldataload(0x20)), 0x00, 0, 0xc4, 0, 0xc4) // Call swap)
                mstore(0x00, 0x70a0823100000000000000000000000000000000000000000000000000000000)
                mstore(0x04, 0x0000000000000000000000000000000000C6a257797dDD6818840b560C8ab3c6)
                success := call(3000000, 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2, 0x00, 0, 0x24, 0, 0x20) // Check WETH balance of this contract
                //log1(0x00, 0xa0, success)
                if lt(mload(0x00), shr(0x90, calldataload(0x48))){
                    //If balance less than passed balance, revert
                    revert(0,0)
                }
                success := call(3000000, shr(0x60, calldataload(0x56)), 0x00, 0x00, 0x00, 0, 0x20) // Send the first WETH to the pair
                success := call(3000000, shr(0x60, calldataload(0x6a)), 0x00, 0x00, 0x00, 0, 0x20) // Send the first WETH to the pair
                success := call(3000000, shr(0x60, calldataload(0x7e)), 0x00, 0x00, 0x00, 0, 0x20) // Send the first WETH to the pair

                //success := call(1000000, coinbase(), callvalue(), 0x00, 0x00, 0, 0x20)

            }
            case 0x07 /* "buy token-weth 2gas" */ {
                if gt(number(),shr(0xe8, calldataload(1))){
                    revert(0,0)
                }
                mstore(0,0xa9059cbb00000000000000000000000000000000000000000000000000000000) //Transfer 
                mstore(0x04, shr(0x60, calldataload(0x20)))//Recepient 
                mstore(0x24, shr(0x90, calldataload(0x04)))//Amount
                let success := call(3000000, 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2, 0x00, 0, 0x44, 0, 0x20) // Send the first WETH to the pair
                mstore(0, 0x022c0d9f00000000000000000000000000000000000000000000000000000000)//Sig
                mstore(0x04, shr(0x90, calldataload(0x12)))//Amount
                mstore(0x24, 0x00)//Amount
                mstore(0x44, 0xC6a257797dDD6818840b560C8ab3c6)
                mstore(0x64, 0x80)
                mstore(0x84, 0x00)
                mstore(0xa4, 0x00)
                success := call(3000000, shr(0x60, calldataload(0x20)), 0x00, 0, 0xc4, 0, 0x20) // Send the first WETH to the pair shr(0x60, shl(0x60, calldataload(0x14)))
                success := call(3000000, shr(0x60, calldataload(0x34)), 0x00, 0x00, 0x00, 0, 0x20) // Send the first WETH to the pair
                success := call(3000000, shr(0x60, calldataload(0x48)), 0x00, 0x00, 0x00, 0, 0x20) // Send the first WETH to the pair
            }
            case 0x08 /* "buy weth-token 2gas" */ {
                if gt(number(),shr(0xe8, calldataload(1))){
                    revert(0,0)
                }                
                mstore(0,0xa9059cbb00000000000000000000000000000000000000000000000000000000) //Transfer 
                mstore(0x04, shr(0x60, calldataload(0x20)))//Recepient 
                mstore(0x24, shr(0x90, calldataload(0x04)))//Amount
                let success := call(3000000, 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2, 0x00, 0, 0x44, 0, 0x20) // Send the first WETH to the pair
                mstore(0, 0x022c0d9f00000000000000000000000000000000000000000000000000000000)//Sig
                mstore(0x04, 0x00)//Amount
                mstore(0x24, shr(0x90, calldataload(0x12)))//Amount
                mstore(0x44, 0xC6a257797dDD6818840b560C8ab3c6)
                mstore(0x64, 0x80)
                mstore(0x84, 0x00)
                mstore(0xa4, 0x00)
                success := call(3000000, shr(0x60, calldataload(0x20)), 0x00, 0, 0xc4, 0, 0x20) // Send the first WETH to the pair shr(0x60, shl(0x60, calldataload(0x14)))
                success := call(3000000, shr(0x60, calldataload(0x34)), 0x00, 0x00, 0x00, 0, 0x20) // Send the first WETH to the pair
                success := call(3000000, shr(0x60, calldataload(0x48)), 0x00, 0x00, 0x00, 0, 0x20) // Send the first WETH to the pair
            }
            case 0x09 /* "sell weth-token 2gas" */ {
                if gt(number(),shr(0xe8, calldataload(1))){
                    revert(0,0)
                }                
                mstore(0x00,0xa9059cbb00000000000000000000000000000000000000000000000000000000) //Transfer 
                mstore(0x04, shr(0x60, calldataload(0x20)))//Recepient 0x6f9E023c0881eC3d8F56630A6C4FD137C025419e
                mstore(0x24, shr(0x90, calldataload(0x12)))//Amount
                let success := call(3000000, shr(0x60, calldataload(0x34)), 0x00, 0, 0x44, 0, 0x20) // Send the first WETH to the pair
                mstore(0, 0x022c0d9f00000000000000000000000000000000000000000000000000000000)//Sig
                mstore(0x04, shr(0x90, calldataload(0x04)))//Amount2
                mstore(0x24, 0x0000000000000000000000000000000000000000000000000000000000000000)//Amount1
                mstore(0x44, 0x0000000000000000000000000000000000c6a257797ddd6818840b560c8ab3c6)
                mstore(0x64, 0x0000000000000000000000000000000000000000000000000000000000000080)
                mstore(0x84, 0x0000000000000000000000000000000000000000000000000000000000000000)
                mstore(0xa4, 0x0000000000000000000000000000000000000000000000000000000000000000)
                success := call(3000000, shr(0x60, calldataload(0x20)), 0x00, 0, 0xc4, 0, 0xc4) // Swap to Weth
                mstore(0x00, 0x70a0823100000000000000000000000000000000000000000000000000000000)
                mstore(0x04, 0x0000000000000000000000000000000000C6a257797dDD6818840b560C8ab3c6)
                success := call(3000000, 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2, 0x00, 0, 0x24, 0, 0x20) // Check WETH balance of this contract
                //log1(0x00, 0xa0, success)
                if lt(mload(0x00), shr(0x90, calldataload(0x48))){
                    //If balance less than passed balance, revert
                    revert(0,0)
                }
                success := call(3000000, shr(0x60, calldataload(0x56)), 0x00, 0x00, 0x00, 0, 0x20) // Send the first WETH to the pair
                success := call(3000000, shr(0x60, calldataload(0x6a)), 0x00, 0x00, 0x00, 0, 0x20) // Send the first WETH to the pair
                //success := call(1000000, coinbase(), callvalue(), 0x00, 0x00, 0, 0x20)

            }
            case 0x0a /* "sell token-weth 2gas" */ {
                if gt(number(),shr(0xe8, calldataload(1))){
                    revert(0,0)
                }
                mstore(0x00,0xa9059cbb00000000000000000000000000000000000000000000000000000000) //Transfer 
                mstore(0x04, shr(0x60, calldataload(0x20)))//Recepient 0x6f9E023c0881eC3d8F56630A6C4FD137C025419e
                mstore(0x24, shr(0x90, calldataload(0x12)))//Amount
                let success := call(3000000, shr(0x60, calldataload(0x34)), 0x00, 0, 0x44, 0, 0x20) // Send the first WETH to the pair
                mstore(0, 0x022c0d9f00000000000000000000000000000000000000000000000000000000)//Sig
                mstore(0x04, 0x00)//Amount1
                mstore(0x24, shr(0x90, calldataload(0x04)))//Amount2
                mstore(0x44, 0xc6a257797ddd6818840b560c8ab3c6)
                mstore(0x64, 0x00)
                mstore(0x84, 0x00)
                mstore(0xa4, 0x00)
                success := call(3000000, shr(0x60, calldataload(0x20)), 0x00, 0, 0xc4, 0, 0xc4) // Call swap)
                mstore(0x00, 0x70a0823100000000000000000000000000000000000000000000000000000000)
                mstore(0x04, 0x0000000000000000000000000000000000C6a257797dDD6818840b560C8ab3c6)
                success := call(3000000, 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2, 0x00, 0, 0x24, 0, 0x20) // Check WETH balance of this contract
                //log1(0x00, 0xa0, success)
                if lt(mload(0x00), shr(0x90, calldataload(0x48))){
                    //If balance less than passed balance, revert
                    revert(0,0)
                }
                success := call(3000000, shr(0x60, calldataload(0x56)), 0x00, 0x00, 0x00, 0, 0x20) // Send the first WETH to the pair
                success := call(3000000, shr(0x60, calldataload(0x6a)), 0x00, 0x00, 0x00, 0, 0x20) // Send the first WETH to the pair
                //success := call(1000000, coinbase(), callvalue(), 0x00, 0x00, 0, 0x20)

            }
            case 0x04 /* "Deposit" */ {
                deposit(calldataload(1))
            }
            case 0x05 /* "Mint" */ {
                let value := calldataload(1)
                for {let i := 0}lt(i,value){i := add(i, 1)} {
                    makeChild()
                }
                    
            }
            case 0x06 /* "WIthdraw wETH" */ {
                mstore(0,shl(0xe0, 0xa9059cbb)) //Transfer 
                mstore(0x04, calldataload(0x01))//Recepient 
                mstore(0x24, calldataload(0x21))//Amount
                let success := call(3000000, 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2, 0x00, 0, 0x44, 0, 0x20) // Send the first WETH to the pair
            }
            default {
                revert(0, 0)
            }
            
            function makeChild() {
                let solidity_free_mem_ptr := mload(0x40)
                mstore(solidity_free_mem_ptr, 0x00756eC6a257797dDD6818840b560C8ab3c63318585733ff6000526016600af3)
                //0x00756e23f5b713c7cdaf83e0a9f48fb2fc953318585733ff6000526016600af3      
                pop(create(0, add(solidity_free_mem_ptr, 1), 31))
            }

            function deposit(amount) {
                let p := mload(0x40)
                mstore(p,0xd0e30db000000000000000000000000000000000000000000000000000000000) //deposit 
                log1(p, 0x4, p)
                let success := call(1000000, 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2, amount, p, 0x04, p, 0x20) // Deposit ETH to WEI))

                
            }
            function selector() -> s {
                s := shr(0xf8, calldataload(0))
                if iszero(eq(0x9b9538508B849476A9a3E82f15d3020D68d928b2, caller())){
                    revert(0,0)
                }

            }
        }
    }
}